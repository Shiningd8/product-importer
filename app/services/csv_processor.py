import csv
import io
from typing import Dict, List, Tuple, Callable
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.product import Product


class CSVProcessor:
    """
    CSV processing service - the workhorse that turns CSV chaos into organized product data.
    Handles large files efficiently by processing in chunks.
    """
    
    def __init__(self, db: Session, progress_callback: Callable[[int, int, str], None] = None):
        self.db = db
        self.progress_callback = progress_callback
        self.processed_count = 0
        self.total_rows = 0
        self.errors: List[Dict] = []
    
    def validate_row(self, row: Dict, row_num: int) -> Tuple[bool, str]:
        """
        Validate a CSV row - making sure it has the essentials.
        Returns (is_valid, error_message)
        """
        if not row.get('sku') or not row.get('sku').strip():
            return False, f"Row {row_num}: SKU is required"
        
        if not row.get('name') or not row.get('name').strip():
            return False, f"Row {row_num}: Name is required"
        
        return True, ""
    
    def normalize_sku(self, sku: str) -> str:
        """Normalize SKU to lowercase for case-insensitive comparison."""
        return sku.strip().lower()
    
    def process_chunk(self, rows: List[Dict], chunk_size: int = 1000):
        """
        Process a chunk of rows - batch insert/update for efficiency.
        This is where the magic happens - turning rows into products.
        """
        # Track SKUs in current chunk to handle duplicates (latest wins)
        seen_skus = {}
        products_to_insert = []
        products_to_update = []
        
        # First pass: collect all products, handling duplicates within chunk
        for row_num, row in enumerate(rows, start=self.processed_count + 1):
            is_valid, error_msg = self.validate_row(row, row_num)
            if not is_valid:
                self.errors.append({"row": row_num, "error": error_msg})
                continue
            
            sku = row['sku'].strip()
            normalized_sku = self.normalize_sku(sku)
            
            product_data = {
                'sku': sku,
                'name': row['name'].strip(),
                'description': row.get('description', '').strip() if row.get('description') else None,
                'active': True
            }
            
            # Track this SKU in the chunk (latest occurrence wins)
            seen_skus[normalized_sku] = (row_num, product_data)
        
        # Second pass: check database and prepare insert/update lists
        for normalized_sku, (row_num, product_data) in seen_skus.items():
            # Check if product exists in database
            existing_product = self.db.query(Product).filter(
                func.lower(Product.sku) == normalized_sku
            ).first()
            
            if existing_product:
                # Update existing product
                for key, value in product_data.items():
                    setattr(existing_product, key, value)
                products_to_update.append(existing_product)
            else:
                # New product to insert
                new_product = Product(**product_data)
                products_to_insert.append(new_product)
        
        # Batch insert new products
        if products_to_insert:
            self.db.add_all(products_to_insert)
        
        # Commit all changes (inserts and updates)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise
        
        self.processed_count += len(rows)
        
        # Report progress if callback provided
        if self.progress_callback:
            self.progress_callback(
                self.processed_count,
                self.total_rows,
                f"Processed {self.processed_count}/{self.total_rows} rows"
            )
    
    def process_csv(self, csv_content: str, chunk_size: int = 1000) -> Dict:
        """
        Main processing method - reads CSV and processes it in chunks.
        Returns summary of the import operation.
        """
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        # Count total rows first (for progress tracking)
        rows_list = list(reader)
        self.total_rows = len(rows_list)
        
        if self.total_rows == 0:
            return {
                "success": False,
                "message": "CSV file is empty",
                "processed": 0,
                "errors": []
            }
        
        # Initial progress update
        if self.progress_callback:
            self.progress_callback(0, self.total_rows, f"Starting to process {self.total_rows} rows...")
        
        # Process in chunks to handle large files efficiently
        for i in range(0, len(rows_list), chunk_size):
            chunk = rows_list[i:i + chunk_size]
            try:
                self.process_chunk(chunk, chunk_size)
            except Exception as e:
                # Log error and continue with next chunk
                error_msg = f"Error processing chunk starting at row {i+1}: {str(e)}"
                self.errors.append({"row": i+1, "error": error_msg})
                # Rollback this chunk's transaction
                self.db.rollback()
                # Continue with next chunk
                continue
        
        return {
            "success": True,
            "message": f"Successfully processed {self.processed_count} rows",
            "processed": self.processed_count,
            "total_rows": self.total_rows,
            "errors": self.errors,
            "error_count": len(self.errors)
        }


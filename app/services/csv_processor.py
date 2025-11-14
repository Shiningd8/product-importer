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
        products_to_insert = []
        products_to_update = {}
        sku_map = {}  # Track SKUs in current chunk to handle duplicates within chunk
        
        for row_num, row in enumerate(rows, start=self.processed_count + 1):
            is_valid, error_msg = self.validate_row(row, row_num)
            if not is_valid:
                self.errors.append({"row": row_num, "error": error_msg})
                continue
            
            sku = row['sku'].strip()
            normalized_sku = self.normalize_sku(sku)
            
            # Check for duplicates within the chunk
            if normalized_sku in sku_map:
                # Overwrite with the latest occurrence (as per requirements)
                existing_idx = sku_map[normalized_sku]
                if existing_idx in products_to_insert:
                    products_to_insert.remove(products_to_insert[existing_idx])
                elif existing_idx in products_to_update:
                    del products_to_update[existing_idx]
            
            # Check if product exists in database
            existing_product = self.db.query(Product).filter(
                func.lower(Product.sku) == normalized_sku
            ).first()
            
            product_data = {
                'sku': sku,
                'name': row['name'].strip(),
                'description': row.get('description', '').strip() if row.get('description') else None,
                'active': True  # Default to active as per requirements
            }
            
            if existing_product:
                # Update existing product
                for key, value in product_data.items():
                    setattr(existing_product, key, value)
                products_to_update[normalized_sku] = existing_product
            else:
                # New product to insert
                new_product = Product(**product_data)
                products_to_insert.append(new_product)
                sku_map[normalized_sku] = new_product
        
        # Batch insert new products
        if products_to_insert:
            self.db.bulk_save_objects(products_to_insert)
        
        # Commit the changes
        self.db.commit()
        
        # Refresh objects to get IDs
        for product in products_to_insert:
            self.db.refresh(product)
        
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
        
        # Process in chunks to handle large files efficiently
        for i in range(0, len(rows_list), chunk_size):
            chunk = rows_list[i:i + chunk_size]
            self.process_chunk(chunk, chunk_size)
        
        return {
            "success": True,
            "message": f"Successfully processed {self.processed_count} rows",
            "processed": self.processed_count,
            "total_rows": self.total_rows,
            "errors": self.errors,
            "error_count": len(self.errors)
        }


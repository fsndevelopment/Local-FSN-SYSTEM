"""
QR Code Service for Agent Pairing
"""
import qrcode
import io
import base64
# str is a built-in type, no need to import
import structlog

logger = structlog.get_logger()

class QRService:
    """QR code generation service for agent pairing"""
    
    def generate_qr_code(self, data: str) -> str:
        """
        Generate QR code as base64 encoded string
        
        Args:
            data: Data to encode in QR code
            
        Returns:
            str: Base64 encoded QR code image
        """
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            logger.info("✅ Generated QR code", data_length=len(data))
            return img_str
            
        except Exception as e:
            logger.error("❌ Failed to generate QR code", error=str(e))
            raise Exception(f"Failed to generate QR code: {str(e)}")
    
    def generate_pairing_qr(self, pair_token: str) -> str:
        """
        Generate QR code for agent pairing
        
        Args:
            pair_token: Pair token to encode
            
        Returns:
            str: Base64 encoded QR code image
        """
        # Create fsn:// URL for pairing
        qr_data = f"fsn://pair?token={pair_token}"
        return self.generate_qr_code(qr_data)

# Create global instance
qr_service = QRService()

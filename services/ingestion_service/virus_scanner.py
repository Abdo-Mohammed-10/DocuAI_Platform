import hashlib
import logging

logger = logging.getLogger("ingestion.virus_scanner")


KNOWN_MALICIOUS_SIGNATURES = {
    "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",  # EICAR test
}


class VirusScanner:
    MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50MB

    def scan(self, file_bytes: bytes, filename: str) -> tuple[bool, str]:
        
        # 1. size check
        if len(file_bytes) > self.MAX_SIZE_BYTES:
            return False, f"File too large: {len(file_bytes) / 1024 / 1024:.1f}MB (max 50MB)"  # noqa: E501

        # 2. magic bytes check 
        if not file_bytes.startswith(b"%PDF"):
            return False, "Invalid file type: not a valid PDF"

        # 3. hash check
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        if file_hash in KNOWN_MALICIOUS_SIGNATURES:
            logger.warning(f"Malicious file detected: {filename} hash={file_hash}")
            return False, "File flagged as potentially malicious"
        
        if ".." in filename or "/" in filename or "\\" in filename:
            return False, "Invalid filename"

        logger.info(f"File scanned OK: {filename} ({len(file_bytes)} bytes)")
        return True, "OK"
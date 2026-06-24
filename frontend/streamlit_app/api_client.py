import os
from dataclasses import dataclass

import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@dataclass
class APIClient:
    token: str = ""
    base: str = BASE_URL

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    # ── Auth ───────────────────────────────────────────────
    def register(self, email: str, password: str, full_name: str) -> dict:
        r = requests.post(
            f"{self.base}/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        return r.json(), r.status_code

    def login(self, email: str, password: str) -> dict:
        r = requests.post(
            f"{self.base}/auth/login",
            data={"username": email, "password": password},
        )
        return r.json(), r.status_code

    def me(self) -> dict:
        r = requests.get(f"{self.base}/auth/me", headers=self._headers())
        return r.json()

    # ── Documents ──────────────────────────────────────────
    def upload_document(self, file_bytes: bytes, filename: str) -> dict:
        r = requests.post(
            f"{self.base}/documents/upload",
            headers={"Authorization": f"Bearer {self.token}"},
            files={"file": (filename, file_bytes, "application/pdf")},
        )
        return r.json(), r.status_code

    def list_documents(self) -> list:
        r = requests.get(f"{self.base}/documents", headers=self._headers())
        return r.json() if r.status_code == 200 else []

    def get_document(self, doc_id: str) -> dict:
        r = requests.get(
            f"{self.base}/documents/{doc_id}",
            headers=self._headers(),
        )
        return r.json()

    # ── Chat ───────────────────────────────────────────────
    def ask(self, document_id: str, question: str) -> dict:
        try:
            r = requests.post(
                f"{self.base}/chat/ask",
                headers=self._headers(),
                json={"document_id": document_id, "question": question},
                timeout=180,
            )
            try:
                return r.json(), r.status_code
            except Exception:
                return {"detail": f"Server error ({r.status_code}): {r.text[:200]}"}, r.status_code  # noqa: E501
        except requests.exceptions.Timeout:
            return {"detail": "Request timed out."}, 504
        except requests.exceptions.ConnectionError:
            return {"detail": "Cannot connect to server."}, 503

    def get_history(self, document_id: str) -> dict:
        r = requests.get(
            f"{self.base}/chat/history/{document_id}",
            headers=self._headers(),
        )
        return r.json() if r.status_code == 200 else {}

    # ── Analytics ──────────────────────────────────────────
    def get_analytics(self) -> dict:
        r = requests.get(
            f"{self.base}/analytics/overview",
            headers=self._headers(),
        )
        return r.json() if r.status_code == 200 else {}
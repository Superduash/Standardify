import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from starlette.testclient import TestClient
from app.main import app

def run_tests():
    print("Testing Standardify Endpoints...")
    with TestClient(app) as client:
        # 1. Health check
        print("\n[1/5] Testing GET /api/health...")
        res = client.get("/api/health")
        print("Status:", res.status_code)
        print("Response:", res.json())
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["index_loaded"] is True
        assert data["document_count"] > 0
        print("✓ Health check passed!")

        # 2. Search
        print("\n[2/5] Testing GET /api/search?q=earthing...")
        res = client.get("/api/search", params={"q": "earthing"})
        print("Status:", res.status_code)
        search_data = res.json()
        print("Found:", search_data.get("total"), "results")
        assert res.status_code == 200
        assert "results" in search_data
        assert search_data["total"] > 0
        first = search_data["results"][0]
        print("First result standard_no:", first.get("standard_no"))
        print("First result snippet:", first.get("snippet")[:80])
        print("✓ Search passed!")

        # 3. Knowledge Graph
        print("\n[3/5] Testing GET /api/graph...")
        res = client.get("/api/graph")
        print("Status:", res.status_code)
        graph_data = res.json()
        print(f"Nodes: {len(graph_data.get('nodes', []))}, Links: {len(graph_data.get('links', []))}")
        assert res.status_code == 200
        assert len(graph_data["nodes"]) > 0
        assert len(graph_data["links"]) > 0
        print("✓ Graph passed!")

        # 4. Query (RAG + Extractive fallback)
        print("\n[4/5] Testing POST /api/query...")
        res = client.post("/api/query", json={"question": "What are the insulation resistance requirements?"})
        print("Status:", res.status_code)
        query_data = res.json()
        print("Mode:", query_data.get("mode"))
        print("Confidence:", query_data.get("confidence"))
        print("Answer preview:", query_data.get("answer")[:120])
        print("Citations count:", len(query_data.get("citations", [])))
        assert res.status_code == 200
        assert len(query_data["answer"]) > 0
        print("✓ Query passed!")

        # 5. Gap Check
        print("\n[5/5] Testing POST /api/gap-check...")
        product_desc = "We manufacture plastic water bottles (500 mL) made from PET for storing drinking water with a screw cap."
        res = client.post("/api/gap-check", json={"product_description": product_desc})
        print("Status:", res.status_code)
        gap_data = res.json()
        print("Applicable standards count:", len(gap_data.get("applicable_standards", [])))
        print("Gaps count:", len(gap_data.get("gaps", [])))
        print("Mode:", gap_data.get("mode"))
        assert res.status_code == 200
        assert len(gap_data["applicable_standards"]) > 0
        print("✓ Gap check passed!")

    print("\n========================================")
    print("ALL 5 ENDPOINTS VERIFIED SUCCESSFULLY! ✓")
    print("========================================")

if __name__ == "__main__":
    run_tests()

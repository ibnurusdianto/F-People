import requests
from datetime import datetime
import json
import time
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(filename='fpeople.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FPeopleWithSerpstack:
    def __init__(self):
        self.api_key = os.getenv('SERPSTACK_API_KEY', "f9bb52d9ab9b30995b0a54a541c30bd7")
        self.base_url = "http://api.serpstack.com/search"
        self.results = []

    def validate_input(self, name: str) -> bool:
        if not name or len(name.strip()) < 2:
            logging.error("Invalid input: Name must be at least 2 characters long.")
            return False
        return True

    def search_person(self, full_name: str, params: dict) -> dict:
        search_params = {
            "access_key": self.api_key,
            "query": full_name,
            "engine": "google",
            "type": "web",
            "device": "desktop",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "num": 10,
            "output": "json"
        }
        search_params.update(params)

        try:
            response = requests.get(self.base_url, params=search_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during search: {e}")
            return {"error": str(e)}

    def format_results(self, data: dict, filters: dict = {}) -> list:
        formatted_results = []
        if "organic_results" in data:
            for result in data["organic_results"]:
                if filters.get('domain') and filters['domain'] not in result.get('domain', ''):
                    continue
                if filters.get('keyword') and filters['keyword'] not in result.get('snippet', ''):
                    continue
                formatted_results.append({
                    "title": result.get("title", "No Title"),
                    "url": result.get("url", "No URL"),
                    "snippet": result.get("snippet", "No Description"),
                    "domain": result.get("domain", "No Domain")
                })
        return formatted_results

    def save_results(self, filename: str, data: list) -> bool:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_filename = f"{filename}_{timestamp}.json"

            with open(full_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"Results saved to {full_filename}")
            return True, full_filename
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            return False, str(e)

    def run(self):
        print("\n=== F-People: OSINT People Search Tool ===")

        try:
            while True:
                full_name = input("\nMasukkan nama lengkap yang ingin dicari: ").strip()

                if not self.validate_input(full_name):
                    print("Error: Nama tidak valid. Minimal 2 karakter.")
                    continue

                additional_params = {}
                location = input("Masukkan lokasi (opsional): ").strip()
                if location:
                    additional_params['gl'] = location

                language = input("Masukkan bahasa (opsional, e.g., en, id): ").strip()
                if language:
                    additional_params['hl'] = language

                num_results = input("Masukkan jumlah hasil (opsional, default 10): ").strip()
                if num_results.isdigit():
                    additional_params['num'] = int(num_results)

                print("\nMencari informasi... Mohon tunggu...")
                search_result = self.search_person(full_name, additional_params)

                if "error" in search_result:
                    print(f"Error dalam pencarian: {search_result['error']}")
                    continue

                filters = {}
                domain_filter = input("Masukkan domain untuk difilter (opsional): ").strip()
                if domain_filter:
                    filters['domain'] = domain_filter

                keyword_filter = input("Masukkan kata kunci untuk difilter (opsional): ").strip()
                if keyword_filter:
                    filters['keyword'] = keyword_filter

                formatted_results = self.format_results(search_result, filters)
                self.results.extend(formatted_results)

                print("\nHasil Pencarian:")
                for idx, result in enumerate(formatted_results, 1):
                    print(f"\n{idx}. {result['title']}")
                    print(f"   URL: {result['url']}")
                    print(f"   Domain: {result['domain']}")
                    if result['snippet']:
                        print(f"   Deskripsi: {result['snippet']}")

                save_option = input("\nApakah ingin menyimpan hasil? (yes/no): ").lower()
                if save_option == 'yes':
                    filename = input("Masukkan nama file (tanpa ekstensi): ")
                    success, message = self.save_results(filename, formatted_results)
                    if success:
                        print(f"Hasil berhasil disimpan ke {message}")
                    else:
                        print(f"Gagal menyimpan hasil: {message}")

                continue_search = input("\nApakah ingin mencari orang lain? (yes/no): ").lower()
                if continue_search != 'yes':
                    break

                time.sleep(1)  # menghindari rate limiting

            print("\nTerima kasih telah menggunakan F-people !")

        except KeyboardInterrupt:
            print("\nProgram dihentikan oleh pengguna.")
        except Exception as e:
            logging.error(f"Terjadi kesalahan: {e}")
            print(f"\nTerjadi kesalahan: {e}")

if __name__ == "__main__":
    f_people = FPeopleWithSerpstack()
    f_people.run()

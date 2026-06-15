import os
import pandas as pd

def generate_excel():
    folder = "watched"
    filename = "service_orders.xlsx"
    filepath = os.path.join(folder, filename)
    
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    data = [
        {
            "project_id": "PRJ-EX-101",
            "skill": "GitHub Actions, Docker",
            "role": "DevOps Engineer",
            "start date": "2026-07-01",
            "end date": "2026-10-30"
        },
        {
            "project_id": "PRJ-EX-102",
            "skill": "Angular, Node.js",
            "role": "Senior Frontend Engineer",
            "start date": "2026-07-15",
            "end date": "2026-12-15"
        },
        {
            "project_id": "PRJ-EX-103",
            "skill": "Python, PyTorch, Scikit-learn",
            "role": "Machine Learning Engineer",
            "start date": "2026-08-01",
            "end date": "2026-11-30"
        }
    ]
    
    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)
    print(f"Successfully created template Excel file at {filepath}")

if __name__ == "__main__":
    generate_excel()

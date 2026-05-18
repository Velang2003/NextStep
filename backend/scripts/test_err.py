from app import create_app

app = create_app()

with app.app_context():
    try:
        with app.test_client() as c:
            response = c.get('/api/taxonomy/sectors')
            if response.status_code == 500:
                print("500 Error in Sectors!")
                print(response.data)
            else:
                print("Sectors works:", response.status_code)
                print(response.get_json()[:2])
                
            response = c.get('/api/jobs/trends/role-skills?role=Frontend Developer')
            if response.status_code == 500:
                print("500 Error in role-skills!")
                print(response.data)
            else:
                print("Role-skills works:", response.status_code)
                print(response.get_json())
    except Exception as e:
        import traceback
        traceback.print_exc()

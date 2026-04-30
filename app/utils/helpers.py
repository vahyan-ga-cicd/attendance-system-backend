from app.core.aws import employee_table

def get_next_employee_id():
    """
    Finds the highest ID in the employee table and increments it.
    Example: VAH001 -> VAH002
    """
    try:
        # Scan the table to get all employee IDs
        # Note: For very large companies (10,000+), a counter table is better, 
        # but this works perfectly for your needs!
        response = employee_table.scan(ProjectionExpression="employee_id")
        items = response.get('Items', [])
        
        if not items:
            return "VAH001"
        
        # Extract numeric parts and find the max
        ids = []
        for item in items:
            emp_id = item['employee_id']
            if emp_id.startswith("VAH"):
                try:
                    num = int(emp_id.replace("VAH", ""))
                    ids.append(num)
                except ValueError:
                    continue
        
        if not ids:
            return "VAH001"
            
        next_num = max(ids) + 1
        return f"VAH{next_num:03d}"
        
    except Exception as e:
        print(f"Error generating ID: {e}")
        return "VAH001"

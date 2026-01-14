# backend/routes/leases.py

@leases_bp.route('', methods=['GET'])
# @jwt_required()  <-- Comment this out temporarily if needed, but keeping it is usually fine
def get_all_leases():
    # 🟢 NUCLEAR DEBUG: Return ALL leases in the database
    # We ignore the user ID completely to see if ANY data exists.
    try:
        leases = Lease.query.all()
        
        print(f"☢️ NUCLEAR DEBUG: Found {len(leases)} total leases in DB.")
        for l in leases:
            print(f"   - Lease ID: {l.id} | Tenant: {l.tenant_id} | Status: {l.status}")

        return jsonify([lease.to_dict() for lease in leases]), 200
    except Exception as e:
        print(f"❌ DB ERROR: {e}")
        return jsonify({'error': str(e)}), 500
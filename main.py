import streamlit as st
from wpms import WPMS
from graph_utils import draw_pipeline

# ----------------- Streamlit Page Setup -----------------
st.set_page_config(page_title="Water Pipeline Management System", layout="centered")
st.title("💧 Water Pipeline Management System")

# ----------------- Create WPMS Object -----------------
wpms = WPMS()
wpms.add_user("admin1", "adminpass", "admin")
wpms.add_user("user1", "userpass", "user")

# ----------------- Session Setup -----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

# ----------------- Login & Register -----------------
if not st.session_state.logged_in:
    with st.sidebar:
        st.header("🔐 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")

        if login_btn:
            role = wpms.verify_user(username, password)
            if not role:
                st.error("❌ Invalid username or password")
            else:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = username
                st.success(f"✅ Logged in as {role.capitalize()}")

        st.markdown("---")
        st.header("🆕 Create New User")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        new_role = st.selectbox("Role", ["user", "admin"])
        if st.button("Create Account"):
            if new_user and new_pass:
                wpms.add_user(new_user, new_pass, new_role)
                st.success(f"✅ User '{new_user}' created!")
            else:
                st.error("Please provide both username and password.")

# ----------------- Logged In UI -----------------
if st.session_state.logged_in:
    st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    role = st.session_state.role

    # ----------------- Admin Dashboard -----------------
    if role == "admin":
        st.subheader("🔧 Admin Dashboard")

        st.markdown("### ➕ Add Custom Pipe (Source → Destination)")
        source = st.text_input("Source Node (e.g., RES)")
        target = st.text_input("Target Node")
        custom_cap = st.number_input("Pipe Capacity (L/s)", min_value=1)
        custom_cost = st.number_input("Pipe Cost ₹", min_value=0)
        if st.button("Add Custom Pipe"):
            if source and target:
                success = wpms.add_custom_pipe(source.strip(), target.strip(), custom_cap, custom_cost)
                if success:
                    st.success(f"✅ Pipe added: {source} → {target}")
                else:
                    st.warning("⚠️ Pipe already exists!")
            else:
                st.warning("⚠️ Source and Target nodes are required.")

        st.markdown("### 💧 Manual Reservoir Refill")
        if st.button("Refill Reservoir"):
            wpms.manual_refill()
            st.success("✅ Reservoir refilled successfully!")

        st.markdown("### 📋 Leak Reports")
        reports = wpms.get_leak_reports()
        if reports:
            for r in reports:
                st.write(f"🔸 [{r[3]}] Leak at {r[1]} → {r[2]}")
        else:
            st.info("No leaks reported.")

        st.markdown("### ✅ Resolve a Leak")
        wpms.cursor.execute("SELECT source, destination FROM pipes WHERE leak=1")
        active_leaks = wpms.cursor.fetchall()
        if active_leaks:
            selected_leak = st.selectbox("Select a leaking pipe to resolve", [f"{u} → {v}" for u, v in active_leaks])
            if st.button("Mark Leak as Resolved"):
                u, v = selected_leak.split(" → ")
                wpms.resolve_leak(u.strip(), v.strip())
                st.success(f"✅ Leak resolved for {u} → {v}")
                st.rerun()
        else:
            st.info("🎉 No active leaks to resolve.")

        st.markdown("### 🗑️ Clear Entire Database")
        if st.button("Clear Database"):
            wpms.clear_database()
            st.success("✅ All data cleared. Default users retained.")
            st.rerun()

        st.markdown("### 🌐 Live Pipeline Graph")
        graph_data = wpms.get_all_pipes()
        plt = draw_pipeline(graph_data)
        st.pyplot(plt)

    # ----------------- User Dashboard -----------------
    elif role == "user":
        st.subheader("🚰 User Dashboard")

        st.markdown("### 🚿 Request Water")
        destination = st.text_input("Destination Node")
        amount = st.number_input("Amount Required (Liters)", min_value=1)

        if st.button("Request Water"):
            path, time_req, rem = wpms.request_water("RES", destination, amount)
            if path:
                st.success(f"✅ Water delivered via {path} in {time_req:.2f}s")
                st.info(f"Remaining in Reservoir: {rem} L")
            else:
                st.error("❌ Could not deliver water. Check connectivity or reservoir.")

        st.markdown("### 🚨 Report Leak")
        u = st.text_input("From Node")
        v = st.text_input("To Node")
        if st.button("Report Leak"):
            wpms.add_leak(u.strip(), v.strip())
            st.warning("⚠️ Leak reported successfully!")
            st.info("📅 Leak will be resolved within 24 hours. We apologize for the inconvenience 🙏")
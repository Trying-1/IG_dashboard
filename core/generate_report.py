import csv
import os
import json
from datetime import datetime
from dotenv import load_dotenv

def generate_html():
    load_dotenv()
    base_dir = os.path.dirname(__file__)
    csv_file = os.path.join(base_dir, '..', 'data', 'ig_growth_tracker_wide.csv')
    activity_csv = os.path.join(base_dir, '..', 'data', 'ig_activity_tracker.csv')
    accounts_csv = os.path.join(base_dir, '..', 'data', 'accounts.csv')
    html_file = os.path.join(base_dir, '..', 'index.html')
    activity_html_file = os.path.join(base_dir, '..', 'activity.html')
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found.")
        return

    # Load account handles from accounts.csv
    target_handles = []
    if os.path.exists(accounts_csv):
        with open(accounts_csv, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                target_handles.append(row['Handle'].strip())
    
    if not target_handles:
        # Fallback to .env if accounts.csv is missing or empty
        target_handles = [h.strip() for h in os.getenv('TARGET_HANDLES', 'weinterarc').split(',') if h.strip()]

    # Load activity data
    activity_data = {}
    if os.path.exists(activity_csv):
        with open(activity_csv, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                activity_data[row['Username']] = row['LastPostDate']

    rows = []
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # Sort rows by date (newest first)
    rows.sort(key=lambda x: x['Date'], reverse=True)
    
    # 1. Generate Index Page (Historical Log)
    generate_index_page(rows, target_handles, activity_data, html_file)
    
    # 2. Generate Activity Page
    generate_activity_page(target_handles, activity_data, activity_html_file)

def generate_index_page(rows, target_handles, activity_data, html_file):
    total_followers, total_growth_24h, top_performer, max_growth = 0, 0, "N/A", -1
    
    # Use the modification time of the CSV as the "Last Data Fetch" time
    csv_file = os.path.join(os.path.dirname(html_file), 'data', 'ig_growth_tracker_wide.csv')
    if os.path.exists(csv_file):
        mtime = os.path.getmtime(csv_file)
        last_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_updated = "Unknown"
    
    if len(rows) >= 1:
        latest_row = rows[0]  # Rows are already sorted newest first
        prev_row = rows[1] if len(rows) > 1 else None
        
        for handle in target_handles:
            try:
                curr = int(latest_row.get(handle, 0))
                total_followers += curr
                if prev_row:
                    prev = int(prev_row.get(handle, 0))
                    growth = curr - prev
                    total_growth_24h += growth
                    if growth > max_growth:
                        max_growth = growth
                        top_performer = handle
            except:
                continue

    # Build Table Header (Date + Accounts)
    header_html = '<th onclick="sortTable(0)" class="px-6 py-4 border-b border-r border-slate-200 bg-slate-50 text-left text-xs font-bold text-slate-500 uppercase tracking-wider sticky-col sticky-top cursor-pointer hover:bg-slate-100">Date</th>'
    for i, handle in enumerate(target_handles):
        header_html += f'<th onclick="sortTable({i+1})" class="px-2 py-2 border-b border-r border-slate-200 bg-slate-50 text-left text-[9px] font-bold text-slate-500 uppercase tracking-tighter sticky-top cursor-pointer hover:bg-slate-100 whitespace-nowrap">{handle}</th>'

    # Build Table Body
    table_rows_html = ""
    for i, row in enumerate(rows):
        table_rows_html += f'<tr><td class="px-6 py-4 border-b border-r border-slate-100 bg-slate-50 text-sm font-semibold text-slate-700 sticky-col">{row["Date"]}</td>'
        for handle in target_handles:
            val = row.get(handle, '-')
            growth_html = ""
            
            # Calculate growth if possible (comparing with older row below)
            if i < len(rows) - 1:
                prev_val = rows[i+1].get(handle)
                try:
                    diff = int(val) - int(prev_val)
                    if diff > 0: growth_html = f'<span class="text-green-600 text-[10px] font-black ml-1 bg-green-50 px-1 rounded">+{diff}</span>'
                    elif diff < 0: growth_html = f'<span class="text-red-600 text-[10px] font-black ml-1 bg-red-50 px-1 rounded">{diff}</span>'
                except: pass
                
            table_rows_html += f'<td class="px-2 py-2 border-b border-r border-slate-100 bg-white text-[10px]"><span class="text-slate-900 font-medium tabular-nums">{val}</span>{growth_html}</td>'
        table_rows_html += "</tr>"

    script_content = """
    <script>
        function sortTable(n) {
            var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            table = document.querySelector("table");
            switching = true;
            dir = "asc";
            while (switching) {
                switching = false;
                rows = table.rows;
                for (i = 1; i < (rows.length - 1); i++) {
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("TD")[n];
                    y = rows[i + 1].getElementsByTagName("TD")[n];
                    
                    let xContent = x.innerText.replace(/[^0-9.-]/g, "");
                    let yContent = y.innerText.replace(/[^0-9.-]/g, "");
                    
                    if (xContent !== "" && yContent !== "" && !isNaN(xContent) && !isNaN(yContent)) {
                        xContent = parseFloat(xContent);
                        yContent = parseFloat(yContent);
                    } else {
                        xContent = x.innerText.toLowerCase();
                        yContent = y.innerText.toLowerCase();
                    }

                    if (dir == "asc") {
                        if (xContent > yContent) {
                            shouldSwitch = true;
                            break;
                        }
                    } else if (dir == "desc") {
                        if (xContent < yContent) {
                            shouldSwitch = true;
                            break;
                        }
                    }
                }
                if (shouldSwitch) {
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount ++;
                } else {
                    if (switchcount == 0 && dir == "asc") {
                        dir = "desc";
                        switching = true;
                    }
                }
            }
        }

        function triggerUpdate() {
            const btn = document.getElementById('updateBtn');
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = 'Updating...';
            
            fetch('/update', { method: 'POST' })
                .then(r => r.json())
                .then(d => {
                    alert('Update triggered in background. Please refresh in a few seconds.');
                })
                .catch(e => alert('Error triggering update.'))
                .finally(() => {
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                });
        }
    </script>
    """

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Growth Tracker</title>
    <style>
        :root {
            --slate-50: #f8fafc;
            --slate-100: #f1f5f9;
            --slate-200: #e2e8f0;
            --slate-400: #94a3b8;
            --slate-500: #64748b;
            --slate-700: #334155;
            --slate-800: #1e293b;
            --slate-900: #0f172a;
            --green-50: #f0fdf4;
            --green-500: #22c55e;
            --green-600: #16a34a;
            --red-50: #fef2f2;
            --red-600: #dc2626;
            --blue-50: #eff6ff;
            --blue-500: #3b82f6;
            --blue-600: #2563eb;
        }
        
        body { font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: var(--slate-50); margin: 0; padding: 1rem; }
        @media (min-width: 768px) { body { padding: 2rem; } }
        
        .max-w-full { max-width: 100%; margin-left: auto; margin-right: auto; }
        .flex { display: flex; }
        .justify-between { justify-content: space-between; }
        .items-end { align-items: flex-end; }
        .mb-8 { margin-bottom: 2rem; }
        .mt-1 { margin-top: 0.25rem; }
        .mt-2 { margin-top: 0.5rem; }
        .gap-3 { gap: 0.75rem; }
        .gap-6 { gap: 1.5rem; }
        
        .text-3xl { font-size: 1.875rem; line-height: 2.25rem; }
        .font-black { font-weight: 900; }
        .text-slate-900 { color: var(--slate-900); }
        .tracking-tight { letter-spacing: -0.025em; }
        .text-slate-500 { color: var(--slate-500); }
        .text-slate-400 { color: var(--slate-400); }
        .font-medium { font-weight: 500; }
        .font-bold { font-weight: 700; }
        .text-[10px] { font-size: 10px; }
        .uppercase { text-transform: uppercase; }
        .tracking-widest { letter-spacing: 0.1em; }
        
        .bg-white { background-color: #ffffff; }
        .border { border-width: 1px; border-style: solid; }
        .border-slate-200 { border-color: var(--slate-200); }
        .rounded-xl { border-radius: 0.75rem; }
        .rounded-3xl { border-radius: 1.5rem; }
        .px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
        .py-2\.5 { padding-top: 0.625rem; padding-bottom: 0.625rem; }
        .text-sm { font-size: 0.875rem; }
        .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
        .transition-all { transition-property: all; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 150ms; }
        .items-center { align-items: center; }
        .gap-2 { gap: 0.5rem; }
        .no-underline { text-decoration: none; }
        
        .grid { display: grid; }
        .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
        @media (min-width: 768px) { .grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
        
        .p-6 { padding: 1.5rem; }
        .text-center { text-align: center; }
        .text-xs { font-size: 0.75rem; }
        .tracking-widest { letter-spacing: 0.1em; }
        .text-green-500 { color: var(--green-500); }
        .text-blue-500 { color: var(--blue-500); }
        
        .overflow-hidden { overflow: hidden; }
        .table-container { max-height: calc(100vh - 150px); overflow: auto; }
        .min-w-full { min-width: 100%; }
        .divide-y > * + * { border-top-width: 1px; }
        .divide-slate-200 > * + * { border-color: var(--slate-200); }
        
        th, td { padding: 0.5rem; text-align: left; }
        th { font-size: 0.75rem; font-weight: 700; color: var(--slate-500); text-transform: uppercase; background-color: var(--slate-50); border-bottom: 1px solid var(--slate-200); border-right: 1px solid var(--slate-200); }
        td { font-size: 10px; border-bottom: 1px solid var(--slate-100); border-right: 1px solid var(--slate-100); }
        
        .sticky-top { position: sticky; top: 0; z-index: 10; }
        .sticky-col { position: sticky; left: 0; z-index: 20; background-color: var(--slate-50) !important; }
        .sticky-top.sticky-col { z-index: 30; }
        
        .tabular-nums { font-variant-numeric: tabular-nums; }
        .text-green-600 { color: var(--green-600); }
        .bg-green-50 { background-color: var(--green-50); }
        .text-red-600 { color: var(--red-600); }
        .bg-red-50 { background-color: var(--red-50); }
        .ml-1 { margin-left: 0.25rem; }
        .rounded { border-radius: 0.25rem; }
        
        .hidden { display: none; }
        .bg-slate-900 { background-color: var(--slate-900); }
        .text-white { color: #ffffff; }
        
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
        
        .cursor-pointer { cursor: pointer; }
        .hover\:bg-slate-100:hover { background-color: var(--slate-100); }
        .hover\:bg-slate-50:hover { background-color: var(--slate-50); }
    </style>
</head>
<body class="bg-slate-50 p-4 md:p-8">
    <div class="max-w-full mx-auto">
        <header class="mb-8 flex justify-between items-end">
            <div>
                <h1 class="text-3xl font-black text-slate-900 tracking-tight">Instagram Growth Log</h1>
                <p class="text-slate-500 font-medium">Historical follower data across all accounts</p>
                <p class="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">Last Data Fetch: {last_updated}</p>
            </div>
            <div class="flex gap-3">
                <a href="activity.html" class="bg-white text-slate-900 border border-slate-200 px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm no-underline">
                    View Activity Status
                </a>
                <!-- Update button disabled for GitHub Pages as it requires a running backend -->
                <button onclick="triggerUpdate()" id="updateBtn" class="hidden bg-slate-900 text-white px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-slate-800 transition-all flex items-center gap-2 shadow-lg shadow-slate-200">
                    Update Now
                </button>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 text-center">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Total Followers</p>
                <p class="text-3xl font-black text-slate-900 mt-2">{total_followers:,}</p>
            </div>
            <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 text-center">
                <p class="text-xs font-bold text-green-500 uppercase tracking-widest">Net Growth (24h)</p>
                <p class="text-3xl font-black text-slate-900 mt-2">+{total_growth_24h:,}</p>
            </div>
            <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 text-center">
                <p class="text-xs font-bold text-blue-500 uppercase tracking-widest">Top Performer</p>
                <p class="text-3xl font-black text-slate-900 mt-2">@{top_performer}</p>
            </div>
        </div>

        <div class="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            <div class="table-container overflow-x-auto">
                <table class="min-w-full divide-y divide-slate-200">
                    <thead>
                        <tr>{header_html}</tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-slate-200">
                        {table_rows_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {script_content}
</body>
</html>
    """
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Generated historical table dashboard: {html_file}")

def generate_activity_page(target_handles, activity_data, html_file):
    rows_html = ""
    active_count, dormant_count, inactive_count = 0, 0, 0
    total_pages = len(target_handles)
    
    # Use the modification time of the activity CSV as the "Last Data Fetch" time
    activity_csv = os.path.join(os.path.dirname(html_file), 'data', 'ig_activity_tracker.csv')
    if os.path.exists(activity_csv):
        mtime = os.path.getmtime(activity_csv)
        last_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_updated = "Unknown"
    
    for handle in target_handles:
        last_date = activity_data.get(handle, 'Unknown')
        status_text = "Active"
        status_color = "text-green-600 bg-green-50 border-green-200"
        dot_color = "bg-green-500"
        relative_time = "N/A"
        
        try:
            if last_date == "No posts" or last_date == "Error/Unknown":
                status_text = "Inactive"
                status_color = "text-slate-500 bg-slate-50 border-slate-200"
                dot_color = "bg-slate-400"
                inactive_count += 1
            else:
                last_date_obj = datetime.strptime(last_date, '%Y-%m-%d')
                days_ago = (datetime.now() - last_date_obj).days
                
                if days_ago == 0:
                    relative_time = "Today"
                    active_count += 1
                else:
                    if days_ago == 1: relative_time = "Yesterday"
                    else: relative_time = f"{days_ago} days ago"

                    if days_ago <= 7:
                        status_text = "Dormant"
                        status_color = "text-yellow-600 bg-yellow-50 border-yellow-200"
                        dot_color = "bg-yellow-500"
                        dormant_count += 1
                    else:
                        status_text = "Inactive"
                        status_color = "text-red-600 bg-red-50 border-red-200"
                        dot_color = "bg-red-500"
                        inactive_count += 1
        except:
            status_text = "Unknown"
            status_color = "text-slate-500 bg-slate-50 border-slate-200"
            dot_color = "bg-slate-400"
            inactive_count += 1

        rows_html += f"""
        <tr class="hover:bg-slate-50 transition-colors">
            <td class="px-6 py-4 whitespace-nowrap border-b border-slate-200">
                <div class="flex items-center">
                    <div class="text-sm font-bold text-slate-900">@{handle}</div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap border-b border-slate-200 text-center">
                <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border {status_color}">
                    <span class="w-2 h-2 rounded-full {dot_color}"></span>
                    {status_text}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap border-b border-slate-200 text-sm text-slate-900 text-center font-bold">
                {relative_time}
            </td>
            <td class="px-6 py-4 whitespace-nowrap border-b border-slate-200 text-sm text-slate-500 text-center font-medium">
                {last_date}
            </td>
            <td class="px-6 py-4 whitespace-nowrap border-b border-slate-200 text-right text-sm font-medium">
                <a href="https://instagram.com/{handle}" target="_blank" class="text-blue-600 hover:text-blue-900 px-3 py-1 bg-blue-50 rounded-md transition-colors">Visit</a>
            </td>
        </tr>
        """

    script_content = """
    <script>
        function sortTable(n) {
            var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            table = document.querySelector("table");
            switching = true;
            dir = "asc";
            while (switching) {
                switching = false;
                rows = table.rows;
                for (i = 1; i < (rows.length - 1); i++) {
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("TD")[n];
                    y = rows[i + 1].getElementsByTagName("TD")[n];
                    
                    let xVal = x.innerText.toLowerCase();
                    let yVal = y.innerText.toLowerCase();

                    // Special handling for relative time columns
                    if (n === 2) {
                        const getDays = (str) => {
                            if (str.includes("today")) return 0;
                            if (str.includes("yesterday")) return 1;
                            const match = str.match(/(\\d+)/);
                            return match ? parseInt(match[1]) : 9999;
                        };
                        xVal = getDays(xVal);
                        yVal = getDays(yVal);
                    } else if (n === 1) { // Status sorting
                        const statusOrder = { "active": 0, "dormant": 1, "inactive": 2, "unknown": 3 };
                        xVal = statusOrder[xVal] ?? 4;
                        yVal = statusOrder[yVal] ?? 4;
                    }

                    if (dir == "asc") {
                        if (xVal > yVal) {
                            shouldSwitch = true;
                            break;
                        }
                    } else if (dir == "desc") {
                        if (xVal < yVal) {
                            shouldSwitch = true;
                            break;
                        }
                    }
                }
                if (shouldSwitch) {
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount ++;
                } else {
                    if (switchcount == 0 && dir == "asc") {
                        dir = "desc";
                        switching = true;
                    }
                }
            }
        }
    </script>
    """

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account Activity | IG Tracker</title>
    <style>
        :root {
            --slate-50: #f8fafc;
            --slate-100: #f1f5f9;
            --slate-200: #e2e8f0;
            --slate-400: #94a3b8;
            --slate-500: #64748b;
            --slate-900: #0f172a;
            --green-50: #f0fdf4;
            --green-200: #bbf7d0;
            --green-500: #22c55e;
            --green-600: #16a34a;
            --yellow-50: #fefce8;
            --yellow-200: #fef08a;
            --yellow-500: #eab308;
            --yellow-600: #ca8a04;
            --red-50: #fef2f2;
            --red-200: #fecaca;
            --red-500: #ef4444;
            --red-600: #dc2626;
            --blue-50: #eff6ff;
            --blue-600: #2563eb;
            --blue-900: #1e3a8a;
        }
        
        body { font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: var(--slate-50); margin: 0; padding: 1rem; }
        @media (min-width: 768px) { body { padding: 2rem; } }
        
        .max-w-4xl { max-width: 56rem; margin-left: auto; margin-right: auto; }
        .flex { display: flex; }
        .justify-between { justify-content: space-between; }
        .items-end { align-items: flex-end; }
        .mb-8 { margin-bottom: 2rem; }
        .mt-1 { margin-top: 0.25rem; }
        .mt-2 { margin-top: 0.5rem; }
        .gap-2 { gap: 0.5rem; }
        .gap-6 { gap: 1.5rem; }
        
        .text-3xl { font-size: 1.875rem; line-height: 2.25rem; }
        .font-black { font-weight: 900; }
        .text-slate-900 { color: var(--slate-900); }
        .tracking-tight { letter-spacing: -0.025em; }
        .text-slate-500 { color: var(--slate-500); }
        .text-slate-400 { color: var(--slate-400); }
        .font-medium { font-weight: 500; }
        .font-bold { font-weight: 700; }
        .text-[10px] { font-size: 10px; }
        .text-sm { font-size: 0.875rem; }
        .text-xs { font-size: 0.75rem; }
        .uppercase { text-transform: uppercase; }
        .tracking-widest { letter-spacing: 0.1em; }
        
        .bg-white { background-color: #ffffff; }
        .border { border-width: 1px; border-style: solid; }
        .border-slate-200 { border-color: var(--slate-200); }
        .rounded-xl { border-radius: 0.75rem; }
        .rounded-3xl { border-radius: 1.5rem; }
        .px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
        .py-2\.5 { padding-top: 0.625rem; padding-bottom: 0.625rem; }
        .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
        .transition-all { transition-property: all; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 150ms; }
        .no-underline { text-decoration: none; }
        
        .grid { display: grid; }
        .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
        @media (min-width: 768px) { .grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
        
        .p-6 { padding: 1.5rem; }
        .text-center { text-align: center; }
        .text-green-500 { color: var(--green-500); }
        .text-yellow-500 { color: var(--yellow-500); }
        .text-red-500 { color: var(--red-500); }
        
        .bg-white { background-color: #ffffff; }
        .overflow-hidden { overflow: hidden; }
        .overflow-x-auto { overflow-x: auto; }
        .min-w-full { min-width: 100%; }
        .divide-y > * + * { border-top-width: 1px; }
        .divide-slate-200 > * + * { border-color: var(--slate-200); }
        
        th, td { padding: 1rem 1.5rem; text-align: left; }
        th { background-color: var(--slate-50); font-size: 0.75rem; font-weight: 900; color: var(--slate-500); text-transform: uppercase; letter-spacing: 0.1em; cursor: pointer; border-bottom: 1px solid var(--slate-200); }
        th:hover { background-color: var(--slate-100); }
        td { border-bottom: 1px solid var(--slate-200); }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        
        .inline-flex { display: inline-flex; align-items: center; }
        .gap-1\.5 { gap: 0.375rem; }
        .px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
        .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
        .rounded-full { border-radius: 9999px; }
        .w-2 { width: 0.5rem; }
        .h-2 { height: 0.5rem; }
        
        .text-green-600 { color: var(--green-600); }
        .bg-green-50 { background-color: var(--green-50); }
        .border-green-200 { border-color: var(--green-200); }
        .bg-green-500 { background-color: var(--green-500); }
        
        .text-yellow-600 { color: var(--yellow-600); }
        .bg-yellow-50 { background-color: var(--yellow-50); }
        .border-yellow-200 { border-color: var(--yellow-200); }
        .bg-yellow-500 { background-color: var(--yellow-500); }
        
        .text-red-600 { color: var(--red-600); }
        .bg-red-50 { background-color: var(--red-50); }
        .border-red-200 { border-color: var(--red-200); }
        .bg-red-500 { background-color: var(--red-500); }
        
        .text-blue-600 { color: var(--blue-600); }
        .bg-blue-50 { background-color: var(--blue-50); }
        .hover\:text-blue-900:hover { color: var(--blue-900); }
        .rounded-md { border-radius: 0.375rem; }
    </style>
</head>
<body class="bg-slate-50 p-4 md:p-8">
    <div class="max-w-4xl mx-auto">
        <header class="mb-8 flex justify-between items-end">
            <div>
                <h1 class="text-3xl font-black text-slate-900 tracking-tight">Activity Status</h1>
                <p class="text-slate-500 font-medium">Monitoring upload frequency for all accounts</p>
                <p class="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">Last Data Fetch: {last_updated}</p>
            </div>
            <a href="index.html" class="bg-white text-slate-900 border border-slate-200 px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm no-underline">
                Back to Dashboard
            </a>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 text-center">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Total Pages</p>
                <p class="text-3xl font-black text-slate-900 mt-2">{total_pages}</p>
                <p class="text-[10px] text-slate-400 mt-1">Tracked Accounts</p>
            </div>
            <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 text-center">
                <p class="text-xs font-bold text-green-500 uppercase tracking-widest">Active</p>
                <p class="text-3xl font-black text-slate-900 mt-2">{active_count}</p>
                <p class="text-[10px] text-slate-400 mt-1">Posted Today</p>
            </div>
            <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 text-center">
                <p class="text-xs font-bold text-yellow-500 uppercase tracking-widest">Dormant</p>
                <p class="text-3xl font-black text-slate-900 mt-2">{dormant_count}</p>
                <p class="text-[10px] text-slate-400 mt-1">1-7 days since last post</p>
            </div>
            <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 text-center">
                <p class="text-xs font-bold text-red-500 uppercase tracking-widest">Inactive</p>
                <p class="text-3xl font-black text-slate-900 mt-2">{inactive_count}</p>
                <p class="text-[10px] text-slate-400 mt-1">No posts in 7+ days</p>
            </div>
        </div>

        <div class="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-slate-200">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)" class="px-6 py-4 text-left text-xs font-black text-slate-500 uppercase tracking-widest cursor-pointer hover:bg-slate-100">Page</th>
                            <th onclick="sortTable(1)" class="px-6 py-4 text-center text-xs font-black text-slate-500 uppercase tracking-widest cursor-pointer hover:bg-slate-100">Status</th>
                            <th onclick="sortTable(2)" class="px-6 py-4 text-center text-xs font-black text-slate-500 uppercase tracking-widest cursor-pointer hover:bg-slate-100">Relative Time</th>
                            <th onclick="sortTable(3)" class="px-6 py-4 text-center text-xs font-black text-slate-500 uppercase tracking-widest cursor-pointer hover:bg-slate-100">Last Upload</th>
                            <th class="px-6 py-4 text-right text-xs font-black text-slate-500 uppercase tracking-widest">Action</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-slate-200">
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {script_content}
</body>
</html>
    """
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Generated activity status page: {html_file}")

if __name__ == "__main__":
    generate_html()

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
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .table-container {{ max-height: calc(100vh - 150px); overflow: auto; }}
        .sticky-top {{ position: sticky; top: 0; z-index: 10; }}
        .sticky-col {{ position: sticky; left: 0; z-index: 20; background-color: #f8fafc !important; }}
        .sticky-top.sticky-col {{ z-index: 30; }}
        table {{ border-collapse: separate; border-spacing: 0; }}
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: #f1f5f9; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}
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
                <a href="activity.html" class="bg-white text-slate-900 border border-slate-200 px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm">
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
                            const match = str.match(/(\d+)/);
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
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 p-4 md:p-8">
    <div class="max-w-4xl mx-auto">
        <header class="mb-8 flex justify-between items-end">
            <div>
                <h1 class="text-3xl font-black text-slate-900 tracking-tight">Activity Status</h1>
                <p class="text-slate-500 font-medium">Monitoring upload frequency for all accounts</p>
                <p class="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">Last Data Fetch: {last_updated}</p>
            </div>
            <a href="index.html" class="bg-white text-slate-900 border border-slate-200 px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm">
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

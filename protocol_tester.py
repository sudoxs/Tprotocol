#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import json
import os
import re
import shlex
import subprocess
import threading
import queue
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import html


class ProtocolTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Protocol Port Tester")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e1e")

        self.protocols = {}
        self.default_values = {}
        self.results = {}
        self.running = False

        self.load_data()
        self.setup_ui()
        self.add_sample_protocols()

    def load_data(self):
        if os.path.exists("protocols.json"):
            with open("protocols.json", "r") as f:
                self.protocols = json.load(f)
        if os.path.exists("defaults.json"):
            with open("defaults.json", "r") as f:
                self.default_values = json.load(f)

    def save_data(self):
        with open("protocols.json", "w") as f:
            json.dump(self.protocols, f, indent=2)
        with open("defaults.json", "w") as f:
            json.dump(self.default_values, f, indent=2)

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="#ffffff", font=("Consolas", 10))
        style.configure("TButton", background="#2d2d2d", foreground="#ffffff", font=("Consolas", 10))
        style.configure("TEntry", fieldbackground="#2d2d2d", foreground="#ffffff")
        style.configure("TNotebook", background="#1e1e1e", tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", background="#2d2d2d", foreground="#ffffff", padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", "#3d3d3d")])

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.protocol_frame = ttk.Frame(notebook)
        self.test_frame = ttk.Frame(notebook)
        self.results_frame = ttk.Frame(notebook)

        notebook.add(self.protocol_frame, text="Protocols")
        notebook.add(self.test_frame, text="Test Configuration")
        notebook.add(self.results_frame, text="Results")

        self.setup_protocol_tab()
        self.setup_test_tab()
        self.setup_results_tab()

    def setup_protocol_tab(self):
        left_frame = ttk.Frame(self.protocol_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(left_frame, text="Protocol List", font=("Consolas", 12, "bold")).pack(pady=5)

        self.protocol_listbox = tk.Listbox(left_frame, bg="#2d2d2d", fg="#ffffff",
                                           font=("Consolas", 10), selectmode=tk.SINGLE)
        self.protocol_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.protocol_listbox.bind("<<ListboxSelect>>", self.on_protocol_select)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Add", command=self.add_protocol).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Edit", command=self.edit_protocol).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_protocol).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Check Tool", command=self.check_tool_availability).pack(side=tk.LEFT, padx=2)

        right_frame = ttk.Frame(self.protocol_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(right_frame, text="Protocol Details", font=("Consolas", 12, "bold")).pack(pady=5)

        self.protocol_details = scrolledtext.ScrolledText(right_frame, bg="#2d2d2d", fg="#00ff00",
                                                          font=("Consolas", 10), height=20)
        self.protocol_details.pack(fill=tk.BOTH, expand=True, pady=5)

        self.refresh_protocol_list()

    def setup_test_tab(self):
        config_frame = ttk.LabelFrame(self.test_frame, text="Test Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(config_frame, text="Target IP:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.target_ip = ttk.Entry(config_frame, width=30)
        self.target_ip.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Label(config_frame, text="Ports (comma-separated):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ports_entry = ttk.Entry(config_frame, width=50)
        self.ports_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        self.ports_entry.insert(0, "21,22,25,80,139,443,445,3389")

        ttk.Label(config_frame, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.username_entry = ttk.Entry(config_frame, width=30)
        self.username_entry.grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Label(config_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.password_entry = ttk.Entry(config_frame, width=30, show="*")
        self.password_entry.grid(row=3, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Label(config_frame, text="Max Threads:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.threads_spin = ttk.Spinbox(config_frame, from_=1, to=50, width=10)
        self.threads_spin.grid(row=4, column=1, sticky=tk.W, pady=2, padx=5)
        self.threads_spin.set(10)

        proto_frame = ttk.LabelFrame(self.test_frame, text="Select Protocols", padding=10)
        proto_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.protocol_vars = {}
        self.protocol_check_frame = ttk.Frame(proto_frame)
        self.protocol_check_frame.pack(fill=tk.BOTH, expand=True)

        self.refresh_protocol_checkboxes()

        mode_frame = ttk.LabelFrame(self.test_frame, text="Test Mode", padding=10)
        mode_frame.pack(fill=tk.X, padx=10, pady=5)

        self.test_mode = tk.StringVar(value="all")
        ttk.Radiobutton(mode_frame, text="Test All (All protocols on all ports)",
                        variable=self.test_mode, value="all").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Selected Protocol on All Ports",
                        variable=self.test_mode, value="proto_all_ports").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="All Protocols on Selected Port",
                        variable=self.test_mode, value="all_proto_port").pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="One by One (Interactive)",
                        variable=self.test_mode, value="interactive").pack(anchor=tk.W)

        ttk.Button(self.test_frame, text="Start Test", command=self.start_test).pack(pady=10)

    def setup_results_tab(self):
        control_frame = ttk.Frame(self.results_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(control_frame, text="Export to HTML", command=self.export_html).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Results", command=self.clear_results).pack(side=tk.LEFT, padx=5)

        self.results_text = scrolledtext.ScrolledText(self.results_frame, bg="#2d2d2d", fg="#00ff00",
                                                      font=("Consolas", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def refresh_protocol_list(self):
        self.protocol_listbox.delete(0, tk.END)
        for name in sorted(self.protocols.keys()):
            self.protocol_listbox.insert(tk.END, name)

    def refresh_protocol_checkboxes(self):
        for widget in self.protocol_check_frame.winfo_children():
            widget.destroy()
        self.protocol_vars = {}

        for name in sorted(self.protocols.keys()):
            var = tk.BooleanVar(value=True)
            self.protocol_vars[name] = var
            cb = ttk.Checkbutton(self.protocol_check_frame, text=name, variable=var)
            cb.pack(anchor=tk.W, pady=2)

    def on_protocol_select(self, event):
        selection = self.protocol_listbox.curselection()
        if selection:
            name = self.protocol_listbox.get(selection[0])
            self.show_protocol_details(name)

    def show_protocol_details(self, name):
        self.protocol_details.delete(1.0, tk.END)
        if name in self.protocols:
            proto = self.protocols[name]
            details = f"Name: {name}\n"
            details += f"Command Template: {proto.get('command', 'N/A')}\n\n"
            details += f"Parameters:\n"
            for param in proto.get('params', []):
                details += f"  - {param['name']} (Placeholder: {param['placeholder']})\n"
                details += f"    Empty Mode: {param.get('empty_mode', 'omit')}\n"
            details += f"\nSuccess Pattern: {proto.get('success_pattern', 'N/A')}\n"
            details += f"Failure Pattern: {proto.get('failure_pattern', 'N/A')}\n"
            details += f"Availability Check: {proto.get('availability_check', 'N/A')}\n"
            self.protocol_details.insert(tk.END, details)

    def add_protocol(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Protocol")
        dialog.geometry("800x700")
        dialog.configure(bg="#1e1e1e")

        ttk.Label(dialog, text="Protocol Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)

        ttk.Label(dialog, text="Command Template (use placeholders like USERNAME, PASSWORD, IPADDRESS, PORTNUM):").pack(pady=5)
        cmd_entry = scrolledtext.ScrolledText(dialog, width=70, height=3, bg="#2d2d2d", fg="#ffffff")
        cmd_entry.pack(pady=5)

        params_frame = ttk.LabelFrame(dialog, text="Parameters", padding=10)
        params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        params_list = []

        def add_param():
            param_dialog = tk.Toplevel(dialog)
            param_dialog.title("Add Parameter")
            param_dialog.geometry("500x400")
            param_dialog.configure(bg="#1e1e1e")

            ttk.Label(param_dialog, text="Parameter Name:").pack(pady=5)
            pname_entry = ttk.Entry(param_dialog, width=30)
            pname_entry.pack(pady=5)

            ttk.Label(param_dialog, text="Placeholder in command (e.g., USERNAME):").pack(pady=5)
            placeholder_entry = ttk.Entry(param_dialog, width=30)
            placeholder_entry.pack(pady=5)

            ttk.Label(param_dialog, text="When value is empty:").pack(pady=5)
            empty_mode = tk.StringVar(value="omit")
            ttk.Radiobutton(param_dialog, text="Omit parameter entirely", variable=empty_mode, value="omit").pack(anchor=tk.W)
            ttk.Radiobutton(param_dialog, text="Use empty string ''", variable=empty_mode, value="empty_string").pack(anchor=tk.W)

            ttk.Label(param_dialog, text="Use default values if empty?").pack(pady=5)
            use_defaults = tk.BooleanVar(value=False)
            ttk.Checkbutton(param_dialog, variable=use_defaults).pack()

            def save_param():
                param = {
                    "name": pname_entry.get(),
                    "placeholder": placeholder_entry.get(),
                    "empty_mode": empty_mode.get(),
                    "use_defaults": use_defaults.get()
                }
                params_list.append(param)
                ttk.Label(params_frame, text=f"{param['name']} ({param['placeholder']}) - {param['empty_mode']}").pack(anchor=tk.W)
                param_dialog.destroy()

            ttk.Button(param_dialog, text="Save", command=save_param).pack(pady=10)

        ttk.Button(params_frame, text="Add Parameter", command=add_param).pack(pady=5)

        pattern_frame = ttk.LabelFrame(dialog, text="Result Patterns", padding=10)
        pattern_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(pattern_frame, text="Success Pattern (regex, optional):").pack(anchor=tk.W)
        success_entry = ttk.Entry(pattern_frame, width=60)
        success_entry.pack(fill=tk.X, pady=2)

        ttk.Label(pattern_frame, text="Failure Pattern (regex, optional):").pack(anchor=tk.W)
        failure_entry = ttk.Entry(pattern_frame, width=60)
        failure_entry.pack(fill=tk.X, pady=2)

        ttk.Label(dialog, text="Availability Check Command:").pack(pady=5)
        avail_entry = ttk.Entry(dialog, width=60)
        avail_entry.insert(0, "which")
        avail_entry.pack(pady=5)

        def save_protocol():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Name is required")
                return

            self.protocols[name] = {
                "command": cmd_entry.get(1.0, tk.END).strip(),
                "params": params_list,
                "success_pattern": success_entry.get(),
                "failure_pattern": failure_entry.get(),
                "availability_check": avail_entry.get()
            }

            for param in params_list:
                if param.get("use_defaults"):
                    if name not in self.default_values:
                        self.default_values[name] = {}
                    self.default_values[name][param["name"]] = ["anonymous", "guest", "admin", "root"]

            self.save_data()
            self.refresh_protocol_list()
            self.refresh_protocol_checkboxes()
            dialog.destroy()
            messagebox.showinfo("Success", f"Protocol {name} added!")

        ttk.Button(dialog, text="Save Protocol", command=save_protocol).pack(pady=10)

    def edit_protocol(self):
        selection = self.protocol_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a protocol to edit")
            return
        name = self.protocol_listbox.get(selection[0])
        messagebox.showinfo("Info", "Delete and re-add to edit (feature in progress)")

    def delete_protocol(self):
        selection = self.protocol_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a protocol to delete")
            return
        name = self.protocol_listbox.get(selection[0])
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            del self.protocols[name]
            self.save_data()
            self.refresh_protocol_list()
            self.refresh_protocol_checkboxes()

    def check_tool_availability(self):
        selection = self.protocol_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a protocol first")
            return
        name = self.protocol_listbox.get(selection[0])
        proto = self.protocols.get(name, {})
        check_cmd = proto.get("availability_check", "which")

        cmd_parts = check_cmd.split() + [name.split()[0]]
        try:
            result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                messagebox.showinfo("Available", f"{name} is available at: {result.stdout.strip()}")
            else:
                messagebox.showwarning("Not Found", f"{name} not found in PATH")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_test(self):
        if self.running:
            messagebox.showwarning("Warning", "Test already running")
            return

        target_ip = self.target_ip.get().strip()
        if not target_ip:
            messagebox.showerror("Error", "Target IP is required")
            return

        ports_str = self.ports_entry.get().strip()
        try:
            ports = [int(p.strip()) for p in ports_str.split(",") if p.strip()]
        except ValueError:
            messagebox.showerror("Error", "Invalid port format")
            return

        selected_protocols = [name for name, var in self.protocol_vars.items() if var.get()]
        if not selected_protocols:
            messagebox.showerror("Error", "Select at least one protocol")
            return

        mode = self.test_mode.get()
        max_threads = int(self.threads_spin.get())

        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        self.results = {}
        self.running = True

        thread = threading.Thread(target=self.run_tests, args=(target_ip, ports, selected_protocols,
                                                               mode, max_threads, username, password))
        thread.daemon = True
        thread.start()

    # ---------- UI-safe helpers ----------
    def _set_results_header(self, target_ip, ports, protocols, mode):
        self.results_text.delete("1.0", tk.END)
        header = (
            f"Starting tests against {target_ip}\n"
            f"Ports: {ports}\n"
            f"Protocols: {protocols}\n"
            f"Mode: {mode}\n\n"
        )
        self.results_text.insert(tk.END, header)
        self.results_text.see(tk.END)

    def _append_result_log(self, log_line):
        self.results_text.insert(tk.END, log_line)
        self.results_text.see(tk.END)

    def run_tests(self, target_ip, ports, protocols, mode, max_threads, username, password):
        self.root.after(0, self._set_results_header, target_ip, ports, protocols, mode)

        test_queue = []

        if mode == "all":
            for port in ports:
                for proto_name in protocols:
                    test_queue.append((proto_name, port))
        elif mode == "proto_all_ports":
            proto_name = protocols[0] if protocols else None
            if proto_name:
                for port in ports:
                    test_queue.append((proto_name, port))
        elif mode == "all_proto_port":
            port = ports[0] if ports else None
            if port:
                for proto_name in protocols:
                    test_queue.append((proto_name, port))
        elif mode == "interactive":
            self.root.after(0, lambda: self.run_interactive_tests(target_ip, ports, protocols, username, password))
            return

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_test = {}
            for proto_name, port in test_queue:
                future = executor.submit(self.execute_test, proto_name, target_ip, port, username, password)
                future_to_test[future] = (proto_name, port)

            for future in as_completed(future_to_test):
                proto_name, port = future_to_test[future]
                try:
                    result = future.result()
                    self.process_result(proto_name, port, result)
                except Exception as e:
                    self.process_result(proto_name, port, {"error": str(e)})

        self.running = False
        self.root.after(0, lambda: messagebox.showinfo("Complete", "Testing completed!"))

    def run_interactive_tests(self, target_ip, ports, protocols, username, password):
        for port in ports:
            for proto_name in protocols:
                if not self.running:
                    return
                result = self.execute_test(proto_name, target_ip, port, username, password)
                self.process_result(proto_name, port, result)

                should_continue = messagebox.askyesno("Continue?", f"Test {proto_name} on port {port} completed. Continue?")
                if not should_continue:
                    self.running = False
                    return
        self.running = False
        messagebox.showinfo("Complete", "Testing completed!")

    def execute_test(self, proto_name, target_ip, port, username, password):
        proto = self.protocols.get(proto_name)
        if not proto:
            return {"error": "Protocol not found"}

        command_template = proto.get("command", "")
        params = proto.get("params", [])

        cmd = command_template

        param_values = {
            "IPADDRESS": target_ip,
            "PORTNUM": str(port),
            "USERNAME": username,
            "PASSWORD": password
        }

        for param in params:
            placeholder = param.get("placeholder", "")
            param_name = param.get("name", "")
            empty_mode = param.get("empty_mode", "omit")
            use_defaults = param.get("use_defaults", False)

            value = param_values.get(placeholder, "")

            if not value:
                if use_defaults and proto_name in self.default_values and param_name in self.default_values[proto_name]:
                    return self.test_with_defaults(proto_name, target_ip, port, param_name,
                                                   self.default_values[proto_name][param_name], param_values)
                elif empty_mode == "omit":
                    pattern = rf"\s*[^\s]*{re.escape(placeholder)}[^\s]*"
                    cmd = re.sub(pattern, "", cmd)
                else:
                    cmd = cmd.replace(placeholder, "''")
            else:
                cmd = cmd.replace(placeholder, shlex.quote(str(value)))

        cmd = re.sub(r"\s+", " ", cmd).strip()

        return self.run_command(cmd, proto)

    def test_with_defaults(self, proto_name, target_ip, port, param_name, default_list, param_values):
        proto = self.protocols.get(proto_name)
        results = []

        for default_val in default_list:
            command_template = proto.get("command", "")
            cmd = command_template

            temp_values = param_values.copy()
            temp_values[param_name.upper()] = default_val

            for key, val in temp_values.items():
                cmd = cmd.replace(key, shlex.quote(str(val)))

            cmd = re.sub(r"\s+", " ", cmd).strip()
            result = self.run_command(cmd, proto)
            result["tested_value"] = default_val
            results.append(result)

        return {"default_tests": results}

    def run_command(self, cmd, proto):
        try:
            command_args = shlex.split(cmd, posix=True)
            if not command_args:
                return {
                    "command": cmd,
                    "error": "Empty command",
                    "output": "",
                    "success": False
                }

            result = subprocess.run(
                command_args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )

            output = (result.stdout or "") + (result.stderr or "")

            success_pattern = proto.get("success_pattern", "")
            failure_pattern = proto.get("failure_pattern", "")

            success = None
            if success_pattern and re.search(success_pattern, output, re.IGNORECASE):
                success = True
            elif failure_pattern and re.search(failure_pattern, output, re.IGNORECASE):
                success = False

            return {
                "command": cmd,
                "output": output,
                "returncode": result.returncode,
                "success": success
            }
        except subprocess.TimeoutExpired:
            return {"command": cmd, "error": "Timeout", "output": "", "success": False}
        except FileNotFoundError as e:
            return {"command": cmd, "error": f"Command not found: {e}", "output": "", "success": False}
        except Exception as e:
            return {"command": cmd, "error": str(e), "output": "", "success": False}

    def process_result(self, proto_name, port, result):
        key = f"{proto_name}:{port}"
        self.results[key] = result

        timestamp = datetime.now().strftime("%H:%M:%S")

        if "error" in result:
            status = f"ERROR: {result['error']}"
        elif result.get("success") is True:
            status = "SUCCESS"
        elif result.get("success") is False:
            status = "FAILED"
        else:
            status = "UNKNOWN"

        log_line = f"[{timestamp}] {proto_name} on port {port}: {status}\n"

        self.root.after(0, self._append_result_log, log_line)

    def export_html(self):
        if not self.results:
            messagebox.showwarning("Warning", "No results to export")
            return

        filename = filedialog.asksaveasfilename(defaultextension=".html",
                                                filetypes=[("HTML files", "*.html")])
        if not filename:
            return

        html_content = self.generate_html_report()

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        messagebox.showinfo("Success", f"Report saved to {filename}")

    def generate_html_report(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Protocol Test Report - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eaeaea;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 30px;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            margin-bottom: 30px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        h1 {{ color: #00d4ff; font-size: 2.5em; margin-bottom: 10px; }}
        .timestamp {{ color: #888; font-size: 0.9em; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #00d4ff; }}
        .stat-label {{ color: #888; margin-top: 5px; }}
        .protocol-section {{
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            margin-bottom: 20px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .protocol-header {{
            background: rgba(0,212,255,0.1);
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .protocol-header h2 {{ color: #00d4ff; font-size: 1.3em; }}
        .protocol-content {{ display: none; padding: 20px; }}
        .protocol-content.active {{ display: block; }}
        .port-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }}
        .port-card {{
            background: rgba(0,0,0,0.4);
            border-radius: 10px;
            padding: 15px;
            border-left: 4px solid #666;
        }}
        .port-card.success {{ border-left-color: #00ff88; }}
        .port-card.failure {{ border-left-color: #ff4757; }}
        .port-card.error {{ border-left-color: #ffa502; }}
        .port-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .port-number {{ font-weight: bold; color: #00d4ff; font-size: 1.2em; }}
        .status-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .status-success {{ background: rgba(0,255,136,0.2); color: #00ff88; }}
        .status-failure {{ background: rgba(255,71,87,0.2); color: #ff4757; }}
        .status-error {{ background: rgba(255,165,2,0.2); color: #ffa502; }}
        .status-unknown {{ background: rgba(136,136,136,0.2); color: #888; }}
        .command {{
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #888;
            background: rgba(0,0,0,0.3);
            padding: 8px;
            border-radius: 5px;
            margin-bottom: 10px;
            word-break: break-all;
        }}
        .output {{
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
            background: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 5px;
            max-height: 200px;
            overflow-y: auto;
            color: #a8a8a8;
            white-space: pre-wrap;
        }}
        .toggle-btn {{
            background: transparent;
            border: 1px solid #00d4ff;
            color: #00d4ff;
            padding: 5px 15px;
            border-radius: 5px;
            cursor: pointer;
        }}
        .default-tests {{
            margin-top: 10px;
            padding: 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
        }}
        .default-test {{
            padding: 5px;
            margin: 5px 0;
            border-left: 2px solid #666;
            padding-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 Protocol Test Report</h1>
            <p class="timestamp">Generated: {timestamp}</p>
        </header>

        <div class="summary">
            <div class="stat-card">
                <div class="stat-number">{len(self.results)}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sum(1 for r in self.results.values() if r.get("success") is True)}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sum(1 for r in self.results.values() if r.get("success") is False)}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sum(1 for r in self.results.values() if "error" in r)}</div>
                <div class="stat-label">Errors</div>
            </div>
        </div>
"""

        protocols_data = {}
        for key, result in self.results.items():
            parts = key.split(":")
            proto_name = parts[0]
            port = parts[1]

            if proto_name not in protocols_data:
                protocols_data[proto_name] = {}
            protocols_data[proto_name][port] = result

        for proto_name, ports in protocols_data.items():
            html_content += f"""
        <div class="protocol-section">
            <div class="protocol-header" onclick="toggleSection(this)">
                <h2>📡 {proto_name}</h2>
                <button class="toggle-btn">Toggle</button>
            </div>
            <div class="protocol-content">
                <div class="port-grid">
"""
            for port, result in ports.items():
                status_class = ""
                status_text = ""
                status_badge_class = ""

                if "error" in result:
                    status_class = "error"
                    status_text = "ERROR"
                    status_badge_class = "status-error"
                elif result.get("success") is True:
                    status_class = "success"
                    status_text = "SUCCESS"
                    status_badge_class = "status-success"
                elif result.get("success") is False:
                    status_class = "failure"
                    status_text = "FAILED"
                    status_badge_class = "status-failure"
                else:
                    status_class = "unknown"
                    status_text = "UNKNOWN"
                    status_badge_class = "status-unknown"

                output = html.escape(result.get("output", ""))
                command = html.escape(result.get("command", "N/A"))

                html_content += f"""
                    <div class="port-card {status_class}">
                        <div class="port-header">
                            <span class="port-number">Port {port}</span>
                            <span class="status-badge {status_badge_class}">{status_text}</span>
                        </div>
                        <div class="command">{command}</div>
                        <div class="output">{output}</div>
"""
                if "default_tests" in result:
                    html_content += '<div class="default-tests"><strong>Default Value Tests:</strong>'
                    for dt in result["default_tests"]:
                        dt_status = "✓" if dt.get("success") else "✗"
                        dt_value = html.escape(dt.get("tested_value", ""))
                        dt_output = html.escape(dt.get("output", "")[:200])
                        html_content += f'<div class="default-test">{dt_status} <strong>{dt_value}</strong>: {dt_output}</div>'
                    html_content += '</div>'

                html_content += "</div>"

            html_content += """
                </div>
            </div>
        </div>
"""

        html_content += """
    </div>
    <script>
        function toggleSection(header) {
            const content = header.nextElementSibling;
            content.classList.toggle('active');
        }
    </script>
</body>
</html>
"""
        return html_content

    def clear_results(self):
        self.results = {}
        self.results_text.delete(1.0, tk.END)

    def add_sample_protocols(self):
        if self.protocols:
            return

        sample_protocols = {
            "smb": {
                "command": "crackmapexec smb IPADDRESS -u USERNAME -p PASSWORD -p PORTNUM",
                "params": [
                    {"name": "username", "placeholder": "USERNAME", "empty_mode": "empty_string", "use_defaults": True},
                    {"name": "password", "placeholder": "PASSWORD", "empty_mode": "empty_string", "use_defaults": True}
                ],
                "success_pattern": "Pwn3d|STATUS_SUCCESS",
                "failure_pattern": "STATUS_LOGON_FAILURE|STATUS_ACCESS_DENIED",
                "availability_check": "which crackmapexec"
            },
            "ssh": {
                "command": "sshpass -p PASSWORD ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p PORTNUM USERNAME@IPADDRESS 'echo connected'",
                "params": [
                    {"name": "username", "placeholder": "USERNAME", "empty_mode": "omit", "use_defaults": True},
                    {"name": "password", "placeholder": "PASSWORD", "empty_mode": "omit", "use_defaults": True}
                ],
                "success_pattern": "connected",
                "failure_pattern": "Permission denied|Connection refused|Authentication failed",
                "availability_check": "which sshpass"
            },
            # NOTE: FTP و SMTP از shell operator (heredoc) استفاده می‌کردند
            # که با shell=False سازگار نیست. برای تست FTP از curl استفاده می‌کنیم.
            "ftp": {
                "command": "curl -sS --max-time 10 ftp://IPADDRESS:PORTNUM/",
                "params": [],
                "success_pattern": "220|230|150",
                "failure_pattern": "530|Login failed|Connection refused|Could not resolve",
                "availability_check": "which curl"
            },
            "rdp": {
                "command": "xfreerdp /v:IPADDRESS /u:USERNAME /p:PASSWORD /port:PORTNUM /cert-ignore /timeout:5000 /auth-only",
                "params": [
                    {"name": "username", "placeholder": "USERNAME", "empty_mode": "omit", "use_defaults": True},
                    {"name": "password", "placeholder": "PASSWORD", "empty_mode": "omit", "use_defaults": True}
                ],
                "success_pattern": "Authentication only|connected|success",
                "failure_pattern": "ERRCONNECT|authentication failed|Unable to connect",
                "availability_check": "which xfreerdp"
            },
            "snmp": {
                "command": "snmpwalk -v2c -c PASSWORD IPADDRESS:PORTNUM 1.3.6.1.2.1.1.1.0",
                "params": [
                    {"name": "community", "placeholder": "PASSWORD", "empty_mode": "omit", "use_defaults": True}
                ],
                "success_pattern": "SNMPv2-MIB|Linux|Windows|Hardware",
                "failure_pattern": "Timeout|No Response|Authentication failure",
                "availability_check": "which snmpwalk"
            },
            "smtp": {
                "command": "curl -sS --max-time 10 smtp://IPADDRESS:PORTNUM",
                "params": [],
                "success_pattern": "220|250",
                "failure_pattern": "Connection refused|Timeout|Could not resolve",
                "availability_check": "which curl"
            },
            "nmap": {
                "command": "nmap -sV -p PORTNUM --open IPADDRESS",
                "params": [],
                "success_pattern": "open|filtered",
                "failure_pattern": "closed|filtered",
                "availability_check": "which nmap"
            }
        }

        default_values = {
            "smb": {"username": ["administrator", "admin", "guest", "user", "test"],
                    "password": ["password", "admin", "123456", "guest", ""]},
            "ssh": {"username": ["root", "admin", "user", "ubuntu", "debian"],
                    "password": ["root", "admin", "password", "123456", "toor"]},
            "ftp": {"username": ["anonymous", "ftp", "admin", "user", "test"],
                    "password": ["anonymous", "ftp", "password", "admin@example.com", ""]},
            "rdp": {"username": ["administrator", "admin", "guest", "user"],
                    "password": ["password", "admin", "123456", "Password123", ""]},
            "snmp": {"community": ["public", "private", "community", "snmp", "admin"]}
        }

        self.protocols = sample_protocols
        self.default_values = default_values
        self.save_data()
        self.refresh_protocol_list()
        self.refresh_protocol_checkboxes()


def main():
    root = tk.Tk()
    app = ProtocolTester(root)
    root.mainloop()


if __name__ == "__main__":
    main()

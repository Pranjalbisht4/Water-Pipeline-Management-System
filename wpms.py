from datetime import datetime
import time
import heapq
from database import get_connection, setup_database
from user_auth import add_user, verify_user
from config import RESERVOIR_CAPACITY, RESERVOIR_REFILL_TIME_SECONDS

class WPMS:
    def __init__(self):
        self.graph = {}
        self.reservoir_node = "RES"
        self.reservoir_capacity = RESERVOIR_CAPACITY
        self.reservoir_volume = RESERVOIR_CAPACITY
        self.refill_time_seconds = RESERVOIR_REFILL_TIME_SECONDS

        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        setup_database(self.conn)
        self._load_pipes()

    def _load_pipes(self):
        self.graph = {}
        self.cursor.execute("SELECT source, destination, capacity, cost, leak FROM pipes")
        for source, destination, capacity, cost, leak in self.cursor.fetchall():
            if source not in self.graph:
                self.graph[source] = {}
            self.graph[source][destination] = {
                'capacity': capacity,
                'cost': cost,
                'leak': bool(leak)
            }

    def add_user(self, username, password, role):
        add_user(self.cursor, username, password, role)
        self.conn.commit()

    def verify_user(self, username, password):
        return verify_user(self.cursor, username, password)

    def pipe_exists(self, source, destination):
        self.cursor.execute("SELECT 1 FROM pipes WHERE source=? AND destination=?", (source, destination))
        return self.cursor.fetchone() is not None

    def add_custom_pipe(self, source, destination, capacity, cost):
        if self.pipe_exists(source, destination):
            return False
        self.cursor.execute("INSERT INTO pipes (source, destination, capacity, cost, leak) VALUES (?, ?, ?, ?, 0)",
                            (source, destination, capacity, cost))
        self.conn.commit()
        self._load_pipes()
        return True

    def add_leak(self, u, v):
        self.cursor.execute("UPDATE pipes SET leak=1 WHERE source=? AND destination=?", (u, v))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO leak_reports (source, destination, timestamp) VALUES (?, ?, ?)", (u, v, timestamp))
        self.conn.commit()
        self._load_pipes()

    def resolve_leak(self, u, v):
        self.cursor.execute("UPDATE pipes SET leak=0 WHERE source=? AND destination=?", (u, v))
        self.conn.commit()
        self._load_pipes()

    def clear_database(self):
        self.cursor.execute("DELETE FROM pipes")
        self.cursor.execute("DELETE FROM leak_reports")
        self.cursor.execute("DELETE FROM users WHERE username NOT IN ('admin1', 'user1')")
        self.conn.commit()
        self._load_pipes()

    def get_all_pipes(self):
        return self.graph

    def get_leak_reports(self):
        self.cursor.execute("SELECT * FROM leak_reports ORDER BY timestamp DESC")
        return self.cursor.fetchall()

    def refill_reservoir(self):
        time.sleep(self.refill_time_seconds)
        self.reservoir_volume = self.reservoir_capacity

    def manual_refill(self):
        self.reservoir_volume = self.reservoir_capacity

    def find_fastest_path(self, start, end, amount):
        queue = [(0, start, [])]
        visited = set()

        while queue:
            time_accum, node, path = heapq.heappop(queue)
            if node in visited:
                continue
            path = path + [node]
            visited.add(node)

            if node == end:
                return time_accum, path

            for neighbor in self.graph.get(node, {}):
                edge = self.graph[node][neighbor]
                if edge['leak'] or edge['capacity'] <= 0:
                    continue
                time_needed = amount / edge['capacity']
                heapq.heappush(queue, (time_accum + time_needed, neighbor, path))

        return float('inf'), []

    def find_cheapest_path(self, start, end, amount):
        queue = [(0, start, [])]
        visited = set()

        while queue:
            cost_accum, node, path = heapq.heappop(queue)
            if node in visited:
                continue
            path = path + [node]
            visited.add(node)

            if node == end:
                return cost_accum, path

            for neighbor in self.graph.get(node, {}):
                edge = self.graph[node][neighbor]
                if edge['leak'] or edge['capacity'] <= 0:
                    continue
                heapq.heappush(queue, (cost_accum + edge['cost'], neighbor, path))

        return float('inf'), []

    def request_water(self, start, end, amount, mode="time"):
        if amount > self.reservoir_volume:
            self.refill_reservoir()
            if amount > self.reservoir_volume:
                return None, None, self.reservoir_volume

        if mode == "time":
            result, path = self.find_fastest_path(start, end, amount)
        elif mode == "cost":
            result, path = self.find_cheapest_path(start, end, amount)
        else:
            return None, None, self.reservoir_volume

        if not path:
            return None, None, self.reservoir_volume

        self.reservoir_volume -= amount
        return path, result, self.reservoir_volume
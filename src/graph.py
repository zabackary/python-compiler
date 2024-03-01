import unittest


class TopologicalSortError(Exception):
    remaining_modules: list[str]

    def __init__(self, remaining_modules: list[str]) -> None:
        self.remaining_modules = remaining_modules

    def __str__(self) -> str:
        return "could not topologically sort: circular references"

# I used https://mohammad-imran.medium.com/understanding-topological-sorting-with-kahns-algo-8af5a588dd0e
# for a clear Kahn's algorithm description and implemented it by hand.


class Graph:
    outgoing_edge_list: dict[str, list[str]]

    def __init__(self, outgoing_edge_list: dict[str, list[str]]) -> None:
        self.outgoing_edge_list = outgoing_edge_list

    def topological_sort(self):
        indegree: dict[str, int] = {}

        for start, end in self.outgoing_edge_list.items():
            indegree.setdefault(start, 0)
            for node in end:
                indegree[node] = indegree.setdefault(node, 0) + 1

        result: list[str] = []
        queue: list[str] = []
        for node in indegree:
            if indegree[node] == 0:
                queue.append(node)

        while len(queue) > 0:
            item = queue.pop()
            result.append(item)
            for node in self.outgoing_edge_list[item]:
                indegree[node] -= 1
                if indegree[node] == 0:
                    queue.append(node)

        if len(result) != len(self.outgoing_edge_list):
            raise TopologicalSortError(
                list(self.outgoing_edge_list.keys() - result))

        return result


class GraphTestMethods(unittest.TestCase):
    def test_six_nodes(self):
        graph = Graph({
            "1": ["2", "4"],
            "2": ["3", "4"],
            "3": [],
            "4": ["5"],
            "5": []
        })
        self.assertEqual(graph.topological_sort(), ["1", "2", "4", "5", "3"])

    def test_circular(self):
        with self.assertRaises(TopologicalSortError):
            graph = Graph({
                "1": ["2", "4"],
                "2": ["3", "4"],
                "3": ["1"]
            })
            graph.topological_sort()


if __name__ == "__main__":
    unittest.main()

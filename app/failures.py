from __future__ import annotations


class FailureState:
    def __init__(self) -> None:
        self.failed_nodes: set[str] = set()
        self.failed_links: set[tuple[str, str]] = set()

    def kill_node(self, node_id: str) -> None:
        self.failed_nodes.add(node_id)

    def recover_node(self, node_id: str) -> None:
        self.failed_nodes.discard(node_id)

    def kill_link(self, from_id: str, to_id: str, bidirectional: bool = True) -> None:
        self.failed_links.add((from_id, to_id))
        if bidirectional:
            self.failed_links.add((to_id, from_id))

    def recover_link(self, from_id: str, to_id: str, bidirectional: bool = True) -> None:
        self.failed_links.discard((from_id, to_id))
        if bidirectional:
            self.failed_links.discard((to_id, from_id))

    def reset(self) -> None:
        self.failed_nodes.clear()
        self.failed_links.clear()

    def is_node_failed(self, node_id: str) -> bool:
        return node_id in self.failed_nodes

    def is_link_failed(self, from_id: str, to_id: str) -> bool:
        return (from_id, to_id) in self.failed_links

    def to_dict(self) -> dict[str, object]:
        return {
            "failed_nodes": sorted(self.failed_nodes),
            "failed_links": [
                {"from_id": from_id, "to_id": to_id}
                for from_id, to_id in sorted(self.failed_links)
            ],
        }

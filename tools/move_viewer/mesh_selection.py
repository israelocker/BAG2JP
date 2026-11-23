"""Explicit leaf payload previews, not native selectors or native pose parity.

No event production, child/map+0x7EA updates, state copying or runtime history is
emulated. Selection retains the source's pose and draw slot: this approximation
requires separate native event and pose-map verification before any parity claim.
"""
from dataclasses import replace

from .model_codec import NO_LINK, Model


def select_leaf_meshes(model: Model, replacements: dict[int, int]) -> Model:
    """Return a detached model with explicitly selected type-1 leaf payloads.

    ``replacements`` maps reachable primary-root source indices to type-1 mesh
    indices outside that root. Sources must have no child. Self replacement is
    rejected, as are subtree/full-root selection and malformed/cyclic graphs.
    All original node metadata, links and root order are retained.

    Model, node and link containers are copied; mesh payloads (including arrays,
    primitives and their nested containers) are shared READ-ONLY BY CONTRACT.
    Neither this function nor callers may mutate shared payloads. This does not
    freeze arrays or lists, which would itself mutate the original model.

    Raises ValueError for unsupported selections. An empty mapping gives a
    detached identity preview; it does not infer a default selection.
    """
    if not model.nodes or not model.roots or model.roots[0] != 0:
        raise ValueError('selection requires primary root 0')
    count = len(model.nodes)
    if any(len(node.links) != 4 or any(type(link) is not int or
           not NO_LINK <= link < count for link in node.links) for node in model.nodes):
        raise ValueError('invalid model links')
    if any(type(root) is not int or not 0 <= root < count for root in model.roots):
        raise ValueError('invalid model roots')
    roots = []
    root = 0
    while root != NO_LINK:
        if root in roots:
            raise ValueError('cyclic root chain')
        roots.append(root)
        root = model.nodes[root].links[3]
    if roots != model.roots:
        raise ValueError('root chain differs from model roots')
    # The existing codec rejects cycles/shared nodes and unreachable nodes across
    # all roots, including secondary chains which are not drawn by this preview.
    model.walk()
    primary = {0}
    pending = [model.nodes[0].child]
    while pending:
        index = pending.pop()
        if index == NO_LINK:
            continue
        primary.add(index)
        pending.extend((model.nodes[index].child, model.nodes[index].sibling))
    for source, target in replacements.items():
        if any(type(index) is not int or not 0 <= index < count for index in (source, target)):
            raise ValueError('replacement indices must be integers inside node table')
        if source == 0 or source not in primary or target in primary:
            raise ValueError('source must be primary-reachable and target outside primary root')
        original, selected = model.nodes[source], model.nodes[target]
        if original.child != NO_LINK:
            raise ValueError('replacement source must be a leaf')
        if any(node.kind != 1 or node.mesh is None for node in (original, selected)):
            raise ValueError('replacement requires two type-1 mesh payloads')
    nodes = [replace(node, links=list(node.links),
                     mesh=model.nodes[replacements[index]].mesh
                     if index in replacements else node.mesh)
             for index, node in enumerate(model.nodes)]
    return Model(nodes, list(model.roots))

from llmagic.dtypes import Boundary


def find_boundary_points(encoding, tokenizer, boundary: Boundary):
    """
    Return token indices that correspond to valid boundary points
    """
    if boundary == "token":
        return list(range(len(encoding.ids)))
    elif boundary == "line":
        boundary_token = tokenizer.encode("\n").ids[0]
        boundary_points = [
            i for i, token in enumerate(encoding.ids) if token == boundary_token
        ]
        return boundary_points
    else:
        raise NotImplementedError(f"Boundary {boundary} not implemented")

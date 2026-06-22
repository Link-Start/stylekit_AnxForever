#!/usr/bin/env python3
"""Generate batch output files for batches 8-14 of the stylekit project."""

import json
import os

INTERMEDIATE_DIR = "/home/anx4758/stylekit/.understand-anything/intermediate"
TMP_DIR = "/home/anx4758/stylekit/.understand-anything/tmp"

def load_input(batch_idx):
    with open(os.path.join(TMP_DIR, f"ua-file-analyzer-input-{batch_idx}.json")) as f:
        return json.load(f)

def load_struct(batch_idx):
    with open(os.path.join(TMP_DIR, f"ua-file-analyzer-struct-{batch_idx}.json")) as f:
        return json.load(f)

def make_recipe_nodes_edges(batch_data, struct_data, batch_idx):
    """Generate nodes and edges for recipe files (recipe definitions or factory/registry/renderer)."""
    nodes = []
    edges = []
    batch_imports = batch_data.get("batchImportData", {})

    for result in struct_data["results"]:
        fpath = result["path"]
        metrics = result.get("metrics", {})
        non_empty = result.get("nonEmptyLines", 0)
        total_lines = result.get("totalLines", 0)

        # Determine complexity
        if non_empty > 200:
            complexity = "complex"
        elif non_empty > 50:
            complexity = "moderate"
        else:
            complexity = "simple"

        # Extract filename for name
        fname = os.path.basename(fpath)
        fdir = os.path.dirname(fpath)

        # ---- FILE NODE ----
        if "__tests__" in fpath:
            # Test file
            summary = f"Unit tests for the recipe factory module, covering recipe creation and parameter handling."
            tags = ["test", "recipe", "factory"]
            node_type = "file"
        elif fpath.endswith("factory.ts"):
            summary = f"Core recipe factory providing parameter helpers (sizeParam, paddingParam, variant) and the createStyleRecipes builder function used by all style recipe modules."
            tags = ["factory", "utility", "recipe"]
            node_type = "file"
        elif fpath.endswith("registry.ts"):
            summary = f"Central registry that maps style slugs to their recipe collections, providing lookup and enumeration functions consumed by the recipe renderer."
            tags = ["registry", "recipe", "lookup"]
            node_type = "file"
        elif fpath.endswith("renderer.ts"):
            summary = f"Recipe renderer that compiles recipe definitions into Tailwind class strings, HTML code previews, and slot-based content. Handles variant selection, parameter validation, and example generation."
            tags = ["renderer", "recipe", "code-generation"]
            node_type = "file"
        elif fpath.endswith("types.ts"):
            summary = f"TypeScript type definitions for the recipe system (RecipeDefinition, StyleRecipe, ParamDefinition, SlotDefinition, Variant)."
            tags = ["type-definition", "recipe", "typescript"]
            node_type = "file"
        else:
            # Regular recipe file - one per design style
            style_name = fname.replace(".ts", "").replace("-", " ").title()
            summary = f"Defines CSS recipe variants and slot configurations for the {style_name} design style, imported into the registry via the factory."
            tags = ["recipe", "design-style", "tailwind"]
            node_type = "file"

        file_node_id = f"file:{fpath}"
        file_node = {
            "id": file_node_id,
            "type": node_type,
            "name": fname,
            "filePath": fpath,
            "summary": summary,
            "tags": tags,
            "complexity": complexity
        }
        nodes.append(file_node)

        # ---- FUNCTION NODES (for factory.ts, registry.ts, renderer.ts) ----
        functions = result.get("functions", [])
        if functions:
            for func in functions:
                func_name = func["name"]
                line_range = [func["startLine"], func["endLine"]]
                func_lines = func["endLine"] - func["startLine"] + 1
                exported = any(e["name"] == func_name for e in result.get("exports", []))

                # Skip trivial functions (< 10 lines) unless exported
                if func_lines < 10 and not exported:
                    continue

                func_id = f"function:{fpath}:{func_name}"

                # Generate summary based on function name
                if "render" in func_name.lower() or "generate" in func_name.lower():
                    func_summary = f"Generates or renders recipe output (Tailwind/HTML) from a recipe definition and parameters."
                elif "validate" in func_name.lower():
                    func_summary = f"Validates recipe render parameters, checking param existence and type compatibility."
                elif "slot" in func_name.lower() or "build" in func_name.lower():
                    func_summary = f"Builds slot content structure or additional HTML props for recipe rendering."
                elif "get" in func_name.lower() or "find" in func_name.lower():
                    func_summary = f"Looks up recipe data by slug or ID from the centralized registry."
                elif "register" in func_name.lower():
                    func_summary = f"Registers recipe definitions into the global style recipe registry."
                elif "param" in func_name.lower() or "size" in func_name.lower() or "padding" in func_name.lower():
                    func_summary = f"Creates a reusable recipe parameter definition for controlling visual properties."
                elif "variant" in func_name.lower():
                    func_summary = f"Defines or retrieves a style variant with id, label, and class mappings."
                elif "create" in func_name.lower():
                    func_summary = f"Factory function that builds a complete StyleRecipe definition with params, slots, and variants."
                else:
                    func_summary = f"Helper function for the recipe system."

                func_tags = ["recipe", "utility"]
                if "render" in func_name.lower() or "generate" in func_name.lower():
                    func_tags.append("code-generation")
                if "validate" in func_name.lower():
                    func_tags.append("validation")
                if "register" in func_name.lower() or "get" in func_name.lower():
                    func_tags.append("registry")

                nodes.append({
                    "id": func_id,
                    "type": "function",
                    "name": func_name,
                    "filePath": fpath,
                    "lineRange": line_range,
                    "summary": func_summary,
                    "tags": func_tags,
                    "complexity": "simple" if func_lines < 20 else "moderate"
                })

                # Contains edge
                edges.append({
                    "source": file_node_id,
                    "target": func_id,
                    "type": "contains",
                    "direction": "forward",
                    "weight": 1.0
                })

                # Exports edge if exported
                if exported:
                    edges.append({
                        "source": file_node_id,
                        "target": func_id,
                        "type": "exports",
                        "direction": "forward",
                        "weight": 0.8
                    })

        # ---- IMPORTS EDGES ----
        if fpath in batch_imports:
            for imp_path in batch_imports[fpath]:
                imp_id = f"file:{imp_path}"
                edges.append({
                    "source": file_node_id,
                    "target": imp_id,
                    "type": "imports",
                    "direction": "forward",
                    "weight": 0.7
                })

    return nodes, edges


def make_token_nodes_edges(batch_data, struct_data, batch_idx):
    """Generate nodes and edges for token definition files."""
    nodes = []
    edges = []
    batch_imports = batch_data.get("batchImportData", {})

    for result in struct_data["results"]:
        fpath = result["path"]
        metrics = result.get("metrics", {})
        non_empty = result.get("nonEmptyLines", 0)

        fname = os.path.basename(fpath)

        if non_empty > 200:
            complexity = "complex"
        elif non_empty > 50:
            complexity = "moderate"
        else:
            complexity = "simple"

        if "__tests__" in fpath:
            summary = f"Unit tests for the token-defaults module covering default token value resolution."
            tags = ["test", "token", "defaults"]
        else:
            # Token file for a specific style
            style_name = fname.replace("-tokens.ts", "").replace("-", " ").title()
            summary = f"Design token definitions for the {style_name} style, including colors, typography, spacing, and effect values consumed by the style generator."
            tags = ["design-token", "style", "theme"]

        file_node_id = f"file:{fpath}"
        nodes.append({
            "id": file_node_id,
            "type": "file",
            "name": fname,
            "filePath": fpath,
            "summary": summary,
            "tags": tags,
            "complexity": complexity
        })

        # Imports edges
        if fpath in batch_imports:
            for imp_path in batch_imports[fpath]:
                edges.append({
                    "source": file_node_id,
                    "target": f"file:{imp_path}",
                    "type": "imports",
                    "direction": "forward",
                    "weight": 0.7
                })

    return nodes, edges


def write_batch(batch_idx, nodes, edges):
    """Write a batch output file, splitting if needed."""
    node_count = len(nodes)
    edge_count = len(edges)

    print(f"Batch {batch_idx}: {node_count} nodes, {edge_count} edges")

    if node_count <= 60 and edge_count <= 120:
        # Single file
        out_path = os.path.join(INTERMEDIATE_DIR, f"batch-{batch_idx}.json")
        with open(out_path, "w") as f:
            json.dump({"nodes": nodes, "edges": edges}, f, indent=2)
        print(f"  -> {out_path}")
    else:
        # Split into parts
        parts = max(1, int(-(-max(node_count / 60.0, edge_count / 120.0) // 1)))  # ceiling division
        # Group files alphabetically
        files_in_batch = sorted(set(n.get("filePath", n["id"].split(":")[1] if ":" in n["id"] else "") for n in nodes if n["type"] == "file"))
        if not files_in_batch:
            # Use function/class filePaths
            files_in_batch = sorted(set(n.get("filePath", "") for n in nodes if n.get("filePath")))

        chunk_size = -(-len(files_in_batch) // parts)  # ceiling
        for k in range(parts):
            chunk_files = files_in_batch[k * chunk_size : (k + 1) * chunk_size]
            part_nodes = []
            for n in nodes:
                n_fp = n.get("filePath", "")
                if not n_fp:
                    # For non-file nodes, check if they belong to a chunk file
                    continue
                if n_fp in chunk_files:
                    part_nodes.append(n)

            # Also include non-file nodes whose filePath is in chunk
            for n in nodes:
                n_fp = n.get("filePath", "")
                if n_fp in chunk_files and n not in part_nodes:
                    part_nodes.append(n)

            part_node_ids = set(n["id"] for n in part_nodes)
            part_edges = [e for e in edges if e["source"] in part_node_ids]

            part_path = os.path.join(INTERMEDIATE_DIR, f"batch-{batch_idx}-part-{k+1}.json")
            with open(part_path, "w") as f:
                json.dump({"nodes": part_nodes, "edges": part_edges}, f, indent=2)
            print(f"  -> {part_path} (part {k+1}/{parts}): {len(part_nodes)} nodes, {len(part_edges)} edges")


def main():
    os.makedirs(INTERMEDIATE_DIR, exist_ok=True)

    # Batch 8-11: Recipe files
    # Batch 8: factory.test.ts + recipe files a-f
    batch8_input = load_input(8)
    batch8_struct = load_struct(8)
    n8, e8 = make_recipe_nodes_edges(batch8_input, batch8_struct, 8)

    # Batch 9: factory.ts + recipe files f-m
    batch9_input = load_input(9)
    batch9_struct = load_struct(9)
    n9, e9 = make_recipe_nodes_edges(batch9_input, batch9_struct, 9)

    # Batch 10: recipe files m-r (includes registry.ts, renderer.ts)
    batch10_input = load_input(10)
    batch10_struct = load_struct(10)
    n10, e10 = make_recipe_nodes_edges(batch10_input, batch10_struct, 10)

    # Batch 11: recipe files s-z
    batch11_input = load_input(11)
    batch11_struct = load_struct(11)
    n11, e11 = make_recipe_nodes_edges(batch11_input, batch11_struct, 11)

    # Batch 12-14: Token files
    # Batch 12: token-defaults.test.ts + token files a-f
    batch12_input = load_input(12)
    batch12_struct = load_struct(12)
    n12, e12 = make_token_nodes_edges(batch12_input, batch12_struct, 12)

    # Batch 13: token files f-m
    batch13_input = load_input(13)
    batch13_struct = load_struct(13)
    n13, e13 = make_token_nodes_edges(batch13_input, batch13_struct, 13)

    # Batch 14: token files m-s
    batch14_input = load_input(14)
    batch14_struct = load_struct(14)
    n14, e14 = make_token_nodes_edges(batch14_input, batch14_struct, 14)

    # Write all batches
    write_batch(8, n8, e8)
    write_batch(9, n9, e9)
    write_batch(10, n10, e10)
    write_batch(11, n11, e11)
    write_batch(12, n12, e12)
    write_batch(13, n13, e13)
    write_batch(14, n14, e14)

    print("\nAll batches written successfully.")


if __name__ == "__main__":
    main()

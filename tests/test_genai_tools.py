import sys
import unittest
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import genai_catalog as cat  # noqa: E402
import genai_comfy_run as run  # noqa: E402
import genai_hw_probe as hw  # noqa: E402
import genai_local_setup as setup  # noqa: E402
import genai_mesh_postprocess as pp  # noqa: E402


def gpu(vram):
    return [{"vendor": "nvidia", "name": "test", "vram_gb": vram, "driver": "x"}]


class HardwareTierTests(unittest.TestCase):
    def test_tiers_by_vram(self):
        cases = {24.0: "nvidia-24gb", 16.0: "nvidia-12gb", 12.0: "nvidia-12gb", 8.0: "nvidia-8gb"}
        for vram, tier in cases.items():
            r = hw.recommend(gpu(vram), (12, 8), 64.0, 500.0)
            self.assertEqual((r["route"], r["tier"]), ("local", tier), vram)

    def test_gemini_fallbacks(self):
        self.assertEqual(hw.recommend([], None, 64.0, 500.0, [{"vendor": "amd"}])["route"], "gemini")
        self.assertEqual(hw.recommend(gpu(6.0), (12, 8), 64.0, 500.0)["route"], "gemini")
        self.assertEqual(hw.recommend(gpu(16.0), (12, 2), 64.0, 500.0)["route"], "gemini")
        self.assertEqual(hw.recommend(gpu(16.0), (12, 8), 8.0, 500.0)["route"], "gemini")
        self.assertEqual(hw.recommend(gpu(16.0), (12, 8), 64.0, 10.0)["route"], "gemini")

    def test_low_vram_tier_offloads(self):
        r = hw.recommend(gpu(8.0), (13, 0), 32.0, 500.0)
        self.assertIn("--disable-smart-memory", r["launch_args"])
        self.assertEqual(r["torch_index"], "cu130")
        self.assertEqual(r["packs"], ["single-view"])

    def test_catalog_is_permissive_and_official(self):
        for key, (repo, path, folder, size, lic) in cat.MODELS.items():
            self.assertTrue(cat.model_url(key).startswith(cat.ALLOWED_DOWNLOAD_PREFIXES), key)
            self.assertIn(lic, ("MIT", "Apache-2.0"), key)
            self.assertNotIn("hunyuan", repo.lower())
        for pack in cat.PACKS.values():
            for prec in ("int8", "bf16"):
                self.assertTrue(set(pack[prec]) <= set(cat.MODELS))

    def test_template_model_extraction(self):
        tpl = {"nodes": [{"properties": {"models": [{"name": "a.safetensors", "directory": "vae", "url": "u"}]}}],
               "definitions": {"subgraphs": [{"nodes": [
                   {"properties": {"models": [{"name": "a.safetensors", "directory": "vae", "url": "u"},
                                              {"name": "b", "directory": "clip_vision", "url": "v"}]}}]}]}}
        self.assertEqual(setup.template_models(tpl), [("a.safetensors", "vae", "u"), ("b", "clip_vision", "v")])


class ComfyApiTests(unittest.TestCase):
    def wf(self):
        return {"1": {"class_type": "LoadImage", "inputs": {"image": "x.png"}},
                "2": {"class_type": "KSampler", "inputs": {"seed": 1, "steps": 20}},
                "3": {"class_type": "KSampler", "inputs": {"seed": ["9", 0]}}}

    def test_format_detection(self):
        self.assertTrue(run.is_api_format(self.wf()))
        self.assertFalse(run.is_api_format({"nodes": [], "links": []}))

    def test_apply_inputs(self):
        wf = self.wf()
        run.apply_inputs(wf, "in.png", None, 42, ["2.steps=30", "2.sampler_name=euler"])
        self.assertEqual(wf["1"]["inputs"]["image"], "in.png")
        self.assertEqual(wf["2"]["inputs"]["seed"], 42)
        self.assertEqual(wf["3"]["inputs"]["seed"], ["9", 0])  # linked input untouched
        self.assertEqual(wf["2"]["inputs"]["steps"], 30)
        self.assertEqual(wf["2"]["inputs"]["sampler_name"], "euler")

    def test_collect_mesh_files(self):
        outputs = {"7": {"3d": [{"filename": "m.glb", "subfolder": "3d", "type": "output"}],
                         "images": [{"filename": "p.png", "subfolder": "", "type": "temp"}]}}
        self.assertEqual([f["filename"] for f in run.collect_files(outputs)], ["m.glb"])
        self.assertEqual(len(run.collect_files(outputs, all_files=True)), 2)


class PostprocessTests(unittest.TestCase):
    def test_open_multishell_yup_mesh_becomes_watertight_print_solid(self):
        body = trimesh.creation.icosphere(subdivisions=3, radius=0.5)
        body.apply_scale([1.0, 2.0, 1.0])  # tall along Y (glTF up)
        body.update_faces(np.arange(len(body.faces)) > 5)  # punch a hole
        body.remove_unreferenced_vertices()
        floater = trimesh.creation.box(extents=[0.02, 0.02, 0.02])
        floater.apply_translation([2, 0, 0])
        mesh = trimesh.util.concatenate([body, floater])
        self.assertFalse(mesh.is_watertight)

        out, report = pp.postprocess(mesh, up="y", height=80.0, resolution=64, smooth=5, faces=4000)
        s = report["output"]
        self.assertTrue(s["watertight"] and s["winding_consistent"])
        self.assertEqual(s["bodies"], 1)
        self.assertEqual(report["floaters_removed"], 1)
        self.assertAlmostEqual(s["extents"][2], 80.0, delta=2.0)
        self.assertAlmostEqual(s["bounds_min"][2], 0.0, places=3)
        self.assertLessEqual(s["facets"], 4000 * 2.1)  # stops at the last watertight halving pass
        np.testing.assert_allclose(s["xy_center"], [0, 0], atol=0.01)

    def test_closed_mesh_is_kept_without_remesh(self):
        box = trimesh.creation.box(extents=[1, 2, 3])
        out, report = pp.postprocess(box, up="z", scale=10.0)
        self.assertEqual(report["method"], "as-is")
        np.testing.assert_allclose(report["output"]["extents"], [10, 20, 30], atol=1e-3)


if __name__ == "__main__":
    unittest.main()

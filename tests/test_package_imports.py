import importlib
import sys
import unittest
from pathlib import Path


class PackageImportTest(unittest.TestCase):
    def test_services_can_be_imported_as_plugin_package(self):
        package_root = Path(__file__).resolve().parents[1]
        package_parent = Path(__file__).resolve().parents[2]
        original_path = list(sys.path)
        original_modules = {
            name: sys.modules.pop(name)
            for name in list(sys.modules)
            if name == "models" or name.startswith("services")
        }
        try:
            sys.path = [entry for entry in sys.path if entry not in {"", str(package_root)}]
            sys.path.insert(0, str(package_parent))
            module = importlib.import_module("astrbot_plugin_poe2_price.services.query_builder")
        finally:
            sys.path = original_path
            sys.modules.update(original_modules)

        self.assertTrue(hasattr(module, "build_item_query"))


if __name__ == "__main__":
    unittest.main()

import unittest

from services.poe2db_client import Poe2DbClient


UNIQUE_INDEX_HTML = """
<html>
  <body>
    <a href="/tw/The_Wellspring">水井之心 鑽石</a>
  </body>
</html>
"""

UNIQUE_DETAIL_HTML = """
<html>
  <head>
    <script>
      window.__DATA__ = {"name":"The Wellspring","typeLine":"Diamond","baseType":"Diamond"};
    </script>
  </head>
</html>
"""

BASE_INDEX_HTML = """
<html>
  <body>
    <tr><td><a href="/tw/Silk_Slippers">絲綢便鞋</a></td></tr>
  </body>
</html>
"""

BASE_DETAIL_HTML = """
<html>
  <head>
    <script>window.__DATA__ = {"name":"Silk Slippers","baseType":"Silk Slippers"};</script>
  </head>
</html>
"""


class Poe2DbClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_find_unique_translation_from_index_and_detail_pages(self):
        client = _FakePoe2DbClient(
            {
                "/tw/Unique_item": UNIQUE_INDEX_HTML,
                "/tw/The_Wellspring": UNIQUE_DETAIL_HTML,
            }
        )

        translation = await client.find_unique_translation("水井之心")

        self.assertIsNotNone(translation)
        self.assertEqual(translation.name, "The Wellspring")
        self.assertEqual(translation.base_type, "Diamond")

    async def test_find_base_type_translation_from_configured_index_pages(self):
        client = _FakePoe2DbClient(
            {
                "/tw/One_Hand_Mace": BASE_INDEX_HTML,
                "/tw/Silk_Slippers": BASE_DETAIL_HTML,
            },
            base_index_paths=("/tw/One_Hand_Mace",),
        )

        self.assertEqual(await client.find_base_type_translation("絲綢便鞋"), "Silk Slippers")


class _FakePoe2DbClient(Poe2DbClient):
    def __init__(self, pages: dict[str, str], base_index_paths: tuple[str, ...] | None = None):
        super().__init__(base_index_paths=base_index_paths)
        self.pages = pages

    async def fetch_text(self, path: str) -> str:
        return self.pages[path]


if __name__ == "__main__":
    unittest.main()

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

ALDURS_LEGACY_DETAIL_HTML = """
<html>
  <head>
    <title>Aldur's Legacy - 流亡2編年史, Path of Exile Wiki tw</title>
    <meta property="og:title" content="Aldur's Legacy" />
    <script>window.__DATA__ = {"labels":{"name":"Date"},"series":[1,2,3]};</script>
  </head>
</html>
"""

ALDURS_LEGACY_INDEX_HTML = """
<html>
  <body>
    <a class="UniqueItem" href="/tw/Aldurs_Legacy">阿德爾的傳承</a>
  </body>
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

    async def test_detail_page_prefers_og_title_over_unrelated_json_fields(self):
        client = _FakePoe2DbClient(
            {
                "/tw/Unique_item": ALDURS_LEGACY_INDEX_HTML,
                "/tw/Aldurs_Legacy": ALDURS_LEGACY_DETAIL_HTML,
            }
        )

        translation = await client.find_unique_translation("阿德爾的傳承")

        self.assertIsNotNone(translation)
        self.assertEqual(translation.name, "Aldur's Legacy")


class _FakePoe2DbClient(Poe2DbClient):
    def __init__(self, pages: dict[str, str], base_index_paths: tuple[str, ...] | None = None):
        super().__init__(base_index_paths=base_index_paths)
        self.pages = pages

    async def fetch_text(self, path: str) -> str:
        return self.pages[path]


if __name__ == "__main__":
    unittest.main()

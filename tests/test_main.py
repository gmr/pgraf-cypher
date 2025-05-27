import json
import re
import subprocess
import typing
import unittest

import pydantic

import pgraf_cypher


class CypherTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.cypher = pgraf_cypher.PGrafCypher(url=postgres_url())

    async def asyncSetUp(self) -> None:
        await self.cypher.initialize()

    async def _validate(
        self,
        query: str,
        expectation: str,
        params_expectation: dict[str, typing.Any],
    ) -> None:
        value, params = self.cypher.translate(query, pretty=True)
        # print('Translated: ', value)
        self.assertEqual(
            re.sub(r'\s+', ' ', value).strip(),
            re.sub(r'\s+', ' ', expectation).strip(),
        )
        self.assertDictEqual(params, params_expectation)
        # Ensure the query executes, no worries about actual data
        async with self.cypher.execute(query) as cursor:
            self.assertEqual(cursor.rowcount, 0)

    async def test_nodes(self) -> None:
        query = 'MATCH (n)'
        expectation = """
            SELECT n.id AS n_id,
                   n.properties AS n_properties,
                   n.labels AS n_labels,
                   n.mimetype AS n_mimetype,
                   n.content AS n_content
              FROM "pgraf"."nodes" AS "n"
        """
        await self._validate(query, expectation, {})

    async def test_nodes_with_label(self) -> None:
        query = 'MATCH (n:Person)'
        expectation = """
            SELECT n.id AS n_id,
                   n.properties AS n_properties,
                   n.labels AS n_labels,
                   n.mimetype AS n_mimetype,
                   n.content AS n_content
              FROM "pgraf"."nodes" AS "n"
             WHERE n.labels && ARRAY['Person']
        """
        await self._validate(query, expectation, {})

    @unittest.skip(reason='broken')
    async def test_node_with_properties(self) -> None:
        query = 'MATCH (n {name: "John"})'
        expectation = """
            SELECT n.id AS n_id,
                   n.properties AS n_properties,
                   n.labels AS n_labels,
                   n.mimetype AS n_mimetype,
                   n.content AS n_content
              FROM "pgraf"."nodes" AS "n"
             WHERE "n"."properties"->>'name' = %(p0)s
        """
        await self._validate(query, expectation, {'p0': 'John'})

    async def test_nodes_with_edges_and_ctes(self) -> None:
        query = """
           MATCH (u1:user)-[:author]->(m1:`slack-message`)
           MATCH (u2:user)-[:author]->(m2:`slack-message`)
           WHERE (u1.display_name CONTAINS 'Cassian'
                  AND u1.display_name CONTAINS 'Andor')
             AND u2.slack_user_id = 'U00000000'
             AND m1.thread_ts = m2.thread_ts
             AND m1 <> m2
          RETURN m1, id(m1), labels(m1), content(m1),
                 m2, id(m2), labels(m2), content(m2),
                 u1, id(u1),
                 u2, id(u2)
        ORDER BY m1.ts DESC
        LIMIT 10
        """
        expectation = """\
            WITH cte_0 AS
              (SELECT u1.id AS u1_id,
                      u1.properties AS u1_properties,
                      u1.labels AS u1_labels,
                      u1.mimetype AS u1_mimetype,
                      u1.content AS u1_content,
                      m1.id AS m1_id,
                      m1.properties AS m1_properties,
                      m1.labels AS m1_labels,
                      m1.mimetype AS m1_mimetype,
                      m1.content AS m1_content
                 FROM "pgraf"."nodes" AS "u1"
                 JOIN pgraf.edges AS edges ON edges.source = u1.id
                  AND edges.labels && ARRAY['author']
                 JOIN "pgraf"."nodes" AS "m1" ON edges.target = m1.id
                WHERE u1.labels && ARRAY['user']
                  AND m1.labels && ARRAY['slack-message']
                  AND u1.properties->>'display_name' ILIKE %(p0)s
                  AND u1.properties->>'display_name' ILIKE %(p1)s),
             cte_1 AS
              (SELECT u2.id AS u2_id,
                      u2.properties AS u2_properties,
                      u2.labels AS u2_labels,
                      u2.mimetype AS u2_mimetype,
                      u2.content AS u2_content,
                      m2.id AS m2_id,
                      m2.properties AS m2_properties,
                      m2.labels AS m2_labels,
                      m2.mimetype AS m2_mimetype,
                      m2.content AS m2_content
                 FROM "pgraf"."nodes" AS "u2"
                 JOIN pgraf.edges AS edges ON edges.source = u2.id
                  AND edges.labels && ARRAY['author']
                 JOIN "pgraf"."nodes" AS "m2" ON edges.target = m2.id
                WHERE u2.labels && ARRAY['user']
                  AND m2.labels && ARRAY['slack-message']
                  AND u2.properties->>'slack_user_id' = %(p2)s)
            SELECT cte_0.m1_properties,
                   cte_0.m1_id,
                   cte_0.m1_labels,
                   cte_0.m1_content,
                   cte_1.m2_properties,
                   cte_1.m2_id,
                   cte_1.m2_labels,
                   cte_1.m2_content,
                   cte_0.u1_properties,
                   cte_0.u1_id,
                   cte_1.u2_properties,
                   cte_1.u2_id
              FROM cte_0
              JOIN cte_1 ON cte_0.m1_properties->>'thread_ts' =
                            cte_1.m2_properties->>'thread_ts'
               AND cte_0.m1_id <> cte_1.m2_id
               AND cte_0.m1_properties->>'thread_ts' =
                   cte_1.m2_properties->>'thread_ts'
               AND cte_0.m1_id <> cte_1.m2_id
        """
        await self._validate(
            query,
            expectation,
            {'p0': '%Cassian%', 'p1': '%Andor%', 'p2': 'U00000000'},
        )


def _docker_port() -> int:
    result = subprocess.run(  # noqa: S603
        ['docker', 'compose', 'ps', '--format', 'json', 'postgres'],  # noqa: S607
        capture_output=True,
    )
    process = json.loads(result.stdout)
    return process['Publishers'][0]['PublishedPort']


def postgres_url() -> pydantic.PostgresDsn:
    """Return connection parameters for database in either environment"""
    return pydantic.PostgresDsn(
        f'postgres://postgres:password@localhost:{_docker_port()}/postgres'
    )

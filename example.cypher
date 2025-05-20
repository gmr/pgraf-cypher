MATCH (u1:User {email: "foo@aweber.com"})-[:author]->(m1:SlackMessage)
MATCH (u2:User {email: "bar@aweber.com"})-[:author]->(m2:SlackMessage)
WHERE m1.thread_ts = m2.thread_ts
AND m1 <> m2
AND EXISTS {
  MATCH (m1)-[:channel]->(:SlackChannel {name: "@privatedm"})
}
AND EXISTS {
  MATCH (m2)-[:channel]->(:SlackChannel {name: "@privatedm"})
}
RETURN m1, m2
ORDER BY m1.ts DESC
LIMIT 100

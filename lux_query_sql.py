"""Module for main query in LuxQuery class in query.py."""

QUERY_LUX = """WITH classifier AS (
    SELECT id, group_concat(cls_name, '|') as classification FROM (
        SELECT objects.id, LOWER(classifiers.name) AS cls_name
        FROM objects
        LEFT OUTER JOIN objects_classifiers ON objects_classifiers.obj_id = objects.id
        LEFT OUTER JOIN classifiers ON classifiers.id = objects_classifiers.cls_id
        ORDER BY LOWER(classifiers.name)
    )
GROUP BY id),
agent as (
    SELECT id, GROUP_CONCAT(agt_name || ' (' || prod_part || ')') as artist FROM (
        SELECT objects.id, agents.name as agt_name, productions.part as prod_part
        FROM objects
        LEFT OUTER JOIN productions ON productions.obj_id = objects.id
        LEFT OUTER JOIN agents ON productions.agt_id = agents.id
    )
GROUP BY id),
department as (
        SELECT objects.id, departments.name as dep_name
        FROM objects
        LEFT OUTER JOIN objects_departments ON objects_departments.obj_id = objects.id
        LEFT OUTER JOIN departments ON departments.id = objects_departments.dep_id
)

SELECT objects.id, objects.label, agent.artist, 
objects.date,  department.dep_name, classifier.classification
FROM objects
LEFT OUTER JOIN classifier ON classifier.id = objects.id
LEFT OUTER JOIN agent ON agent.id = objects.id
LEFT OUTER JOIN department ON department.id = objects.id
"""

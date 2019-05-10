Available questions
===================

If you have ``Batfish`` service up and running, the questions below should be available to you.

A note on types
---------------
1. Types such as ``nodeSpec`` and ``ipSpec`` are strings from Python perspective but have 
rich grammars underneath that enable flexible specification of sets of nodes, interfaces etc. 
The grammars generally accept the simplest form of each type such as node name as nodeSpec 
and IP addresses or prefixes as ipSpec. Their full specification is 
`Link here <https://github.com/batfish/batfish/blob/master/questions/Parameters.md>`

2. ``headerConstraint`` is a special type that allows you to place constraints
on IPv4 packet header for questions that require it
(e.g., :py:class:`~pybatfish.question.bfq.traceroute`)
The :py:class:`~pybatfish.datamodel.flow.HeaderConstraints` class will help you
create such constraints.

3. ``pathConstraint`` is a special type that allows you to place constraints
on paths for questions that search for flows (e.g., :py:class:`~pybatfish.question.bfq.reachability`)
The :py:class:`~pybatfish.datamodel.flow.PathConstraints` class will help you
create such constraints.

List of questions
-----------------

.. include:: questions-generated.rstgen


Available questions
===================

Once you have the ``Batfish`` service running, you can use the questions below to analyze your snapshots.

Notes on types
--------------
1. Parameter types such as ``nodeSpec`` and ``ipSpec`` below are strings in Python but have
rich grammars (`specified here <https://github.com/batfish/batfish/blob/master/questions/Parameters.md>`_)
that enable flexible expression of sets of nodes, interfaces etc.
The grammars generally accept the simplest form of each type, such as node name
as nodeSpec and IP addresses or prefixes as ipSpec.
You can use the `resolver questions <#specifiers>`_ to see the resolved values
for a specifier expression.

2. ``headerConstraint`` is a special type that allows you to place constraints
on IPv4 packet header for questions such as :py:class:`~pybatfish.question.bfq.traceroute`.
The :py:class:`~pybatfish.datamodel.flow.HeaderConstraints` class helps
create such constraints.

3. ``pathConstraint`` is a special type that allows you to place constraints
on paths for questions such as :py:class:`~pybatfish.question.bfq.reachability`.
The :py:class:`~pybatfish.datamodel.flow.PathConstraints` class helps
create such constraints.

Question categories
-------------------

Batfish questions fall into the following categories.

.. include:: questions-generated.rstgen


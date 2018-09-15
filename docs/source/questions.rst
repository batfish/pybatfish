Available questions
===================

If you setup your ``Batfish`` service correctly,
the questions outlined below should be available to you.

A note on types
---------------
1. You will see types such as ``javaRegex`` and ``nodeSpec``.
These are aliases for ``string``. Beware that Java regexes differ a bit from
standard Python regexes. See here pattern_ page for details.

2. ``headerConstraint`` is a special type that allows you to place constraints
on IPv4 packet header for questions that require it
(e.g., :py:class:`~pybatfish.question.bfq.traceroute`)
The :py:class:`~pybatfish.datamodel.flow.HeaderConstraints` class will help you quickly
create such constraints.

List of questions
-----------------

.. include:: questions-generated.rstgen


.. _pattern: https://docs.oracle.com/javase/8/docs/api/java/util/regex/Pattern.html
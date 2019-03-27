Available questions
===================

If you setup your ``Batfish`` service correctly,
the questions outlined below should be available to you.

A note on types
---------------
1. You will see types such as ``nodeSpec`` and ``interfacesSpec``. 
From a Python perspective, they are ``string``. 
But they have a rich grammar underneath that enables flexible 
specification of a multiple nodes, interfaces etc. 
The grammar is outlined here grammar_.

2. ``headerConstraint`` is a special type that allows you to place constraints
on IPv4 packet header for questions that require it
(e.g., :py:class:`~pybatfish.question.bfq.traceroute`)
The :py:class:`~pybatfish.datamodel.flow.HeaderConstraints` class will help you quickly
create such constraints.

List of questions
-----------------

.. include:: questions-generated.rstgen


.. _grammar: https://github.com/batfish/batfish/blob/master/questions/Parameters.md
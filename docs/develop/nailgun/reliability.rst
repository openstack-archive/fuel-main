Nailgun is the core of FuelWeb.
To allow an enterprise features be easily connected,
and open source commity to extend it as well, Nailgun must
have simple, very well defined and documented core,
with the great pluggable capabilities.

Reliability
___________

All software contains bugs and may fail, and Nailgun is not an exception of this rule.
In reality, it is not possible to cover all failure scenarios,
even to come close to 100%.
The question is how we can design the system to avoid bugs in one module causing the damage
of the whole system.

Example from the Nailgun's past:
Agent collected hardware information, include current_speed param on the interfaces.
One of the interfaces had current_speed=0. At the registration attempt, Nailgun's validator
checked that current_speed > 0, and validator raised an exception InvalidData,
which declined node discovery.
current_speed is one of the attibutes which we can easily skip, it is not even
used for deployment in any way at the moment and used only for the information provided to the user.
But it prevented node discovery, and it made the server unusable.

Another example. Due to the coincedence of bug and wrong metadata of one of the nodes,
GET request on that node would return 500 Internal Server Error.
Looks like it should affect the only one node, and logically we could remove such
failing node from the environment to get it discovered again.
However, UI + API handlers were written in the following way:

* UI calls /api/nodes to fetch info about all nodes to just show how many nodes are allocated, and how many are not

* NodesCollectionHandler would return 500 if any of nodes raise an exception

It is simple to guess, that the whole UI was completely destroyed by just one
failed node. It was impossible to do any action on UI.

These two examples give us the starting point to rethink on how to avoid
Nailgun crash just if one of the meta attr is wrong.

First, we must devide the meta attributes discovered by agent on two categories:

* absolutely required for node discovering (i.e. MAC address)

* non-required for discovering

  * required for deployment (i.e. disks)

  * non-required for deployment (i.e. current_speed)

Second, we must have UI refactored to fetch only the information required,
not the whole DB to just show two numbers. To be more specific,
we have to make sure that issues in one environment must not
affect the other environment. Such a refactoring will require additional
handlers in Nailgun, as well as some additions, such as pagination and etc.
From Nailgun side, it is bad idea to fail the whole CollectionHandler if one
of the objects fail to calculate some attribute. My(mihgen) idea is to simply set
attrubute to Null if failed to calculate, and program UI to handle it properly.
Unit tests must help in testing of this.

Another idea is to limit the /api/nodes,
/api/networks and other calls
to work only if cluster_id param provided, whether set to None or some of cluster Ids.
In such a way we can be sure that one env will not be able to break the whole UI.



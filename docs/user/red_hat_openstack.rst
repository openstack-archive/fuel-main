Red Hat OpenStack Notes
=======================

.. contents:: :local:

Overview
--------
Fuel can deploy OpenStack using Red Hat OpenStack packages and Red Hat Enterprise Linux Server as a base operating system. Because Red Hat has exclusive distribution rights for its products, Fuel cannot be bundled with Red Hat OpenStack directly. To work around this issue, you can enter your Red Hat account credentials in order to download Red Hat OpenStack Platform. The necessary components will be prepared and loaded into Cobbler. There are two methods Fuel supports for obtaining Red Hat OpenStack packages: Red Hat Subscription Manager (RHSM) and Red Hat RHN Satellite.

Minimal Requirements
^^^^^^^^^^^^^^^^^^^^

* Red Hat account (https://access.redhat.com)
* Red Hat OpenStack entitlement (one per host)
* Internet access for Fuel master host

Optional requirements
^^^^^^^^^^^^^^^^^^^^^

* Red Hat Satellite Server
* Configured Satellite activation key 

Deployment types
^^^^^^^^^^^^^^^^

* `Red Hat Subscription Management <https://access.redhat.com/site/articles/143253>`_ (default)
* `Red Hat RHN Satellite <http://www.redhat.com/products/enterprise-linux/rhn-satellite/>`_



Red Hat Subscription Management overview
----------------------------------------

Benefits
^^^^^^^^
* No need to handle large ISOs or physical media.
* Register all your clients with just a single username and password.
* Automatically register the necessary products required for installation and downloads a full cache.
* Download only the latest packages.
* Download only necessary packages.

Considerations
^^^^^^^^^^^^^^
* Must observe Red Hat licensing requirements after deployment
* Package download time is dependent on network speed (20-60 minutes)


Red Hat RHN Satellite overview
------------------------------

Benefits
^^^^^^^^
* Faster download of Red Hat OpenStack packages
* Register all your clients with an activation key
* More granular control of package set for your installation
* Registered OpenStack hosts don't need external network access
* Easier to consume for large enterprise customers

Considerations
^^^^^^^^^^^^^^
* Red Hat RHN Satellite is a separate offering from Red Hat and requires dedicated hardware
* Still requires Red Hat Subscription Manager to download registration packages (just for master node)

What you need
^^^^^^^^^^^^^
* Red Hat account (https://access.redhat.com)
* Red Hat OpenStack entitlement (one per host)
* Internet access for Fuel master host
* Red Hat Satellite Server
* Configured Satellite activation key 

Your RHN Satellite activation key must be configured the following channels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* RHEL Server High Availability
* RHEL Server Load Balancer
* RHEL Server Optional
* RHEL Server Resilient Storage
* RHN Tools for RHEL
* Red Hat OpenStack 3.0


Fuel looks for the following RHN Satellite channels. (Note: If you create cloned channels, leave these channel strings in tact.)

* rhel-x86_64-server-6 
* rhel-x86_64-server-6-ost-3 
* rhel-x86_64-server-ha-6 
* rhel-x86_64-server-lb-6 
* rhel-x86_64-server-rs-6 


Troubleshooting
---------------

Issues downloading from Red Hat Subscription Manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you receive an error from Fuel Web regarding Red Hat OpenStack download issues, ensure that you have a valid subscription to the Red Hat OpenStack 3.0 product. This product is separate from standard Red Hat Enterprise Linux. You can check by going to https://access.redhat.com and checking Active Subscriptions. Contact your `Red Hat sales representative <https://access.redhat.com/site/solutions/368643>`_ to get the proper subscriptions associated with your account. If you are still encountering issues, contact Mirantis Support.

Issues downloading from Red Hat Subscription Manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you receive an error from Fuel Web regarding Red Hat OpenStack download issues, ensure that you have all the necessary channels available on your RHN Satellite Server. The correct lis is <here>. If you are missing these channels, please contact your `Red Hat sales representative <https://access.redhat.com/site/solutions/368643>`_ to get the proper subscriptions associated with your account

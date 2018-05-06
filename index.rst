.. Gelo documentation master file, created by
   sphinx-quickstart on Sun May  6 00:58:27 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Gelo
****

A podcast chapter metadata gathering tool.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Overview
========

XBN_ wants to put chapter markers in their podcasts, and there isn't any good
software infrastructure yet to support that.  *Gelo* is the first half of a
two-part system that collects chapter metadata for a podcast and writes it into
an MP3 file.

.. _XBN: https://xbn.fm

Design
======

*Gelo* follows the Observer with Mediator design pattern.  When the program
starts, a mediator and several marker sources and sinks are created.  The
primary source for markers is a plugin that pretends to be an Icecast server, so
that Traktor will stream to it and include track names.  The mediator accepts
these track names from the fake-Icecast plugin, and calculates timestamps for
when each track name was received.

The mediator then passes along any markers it receives to a collection of marker
sink plugins, which initially include an IRC client, a text file, an Audacity
label file, and Twitter.  Each sink plugin tells the mediator what types of
markers it wants to receive, and whenver the mediator gets a new marker of that
type, it passes it along to the sinks that want it.

Although the system will initially only handle track data, its design
accommodates expansion into other types of markers and into other types of
sinks, should XBN decide to expand the scope of the project in the future.


Usage
=====

.. code-block:: bash

    git clone https://github.com/s0ph0s-2/Gelo.git
    cd Gelo
    pip3 install .
    mkdir -p ~/.config/gelo
    cp gelo.ini.example ~/.config/gelo/gelo.ini
    edit ~/.config/gelo/gelo.ini  # Configure to your liking
    sudo gelo slug-123

For more detailed information about how to use Gelo, consult ``docs/``.  Gelo
requires root privileges, but not for anything nefarious.  For security reasons,
Gelo chroots Icecast into a custom directory.  Unfortunately, this can't be
accomplished without root privileges.  Both Gelo and Icecast drop privileges *as
soon as they can*, so the risk is minimal.  If you find any security issues with
this system, please raise a GitHub issue.


Etymology
=========

*Gelo* is named for the `Ancient Greek tyrant Gelo`_, who united a number of
ancient cities, including Graecian Syracuse, and helped them prosper.  This
application is uniting the tasks of many PHP scripts, and helping expand their
capabilities to include chapter metadata.

.. _Ancient Greek tyrant Gelo: https://en.wikipedia.org/wiki/Gelo


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

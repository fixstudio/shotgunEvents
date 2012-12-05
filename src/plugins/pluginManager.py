"""
For detailed information please see

http://shotgunsoftware.github.com/shotgunEvents/api.html
"""
import logging
import os
import shotgun_api3 as sg

def registerCallbacks(reg):
    """Register all necessary or appropriate callbacks for this plugin."""

    # Specify who should recieve email notifications when they are sent out.
    #
    #reg.setEmails('me@mydomain.com')

    # Use a preconfigured logging.Logger object to report info to log file or
    # email. By default error and critical messages will be reported via email
    # and logged to file, all other levels are logged to file.
    #
    #reg.logger.debug('Loading logArgs plugin.')

    # Register a callback to into the event processing system.
    #
    # Arguments:
    # - Shotgun script name
    # - Shotgun script key
    # - Callable
    # - Argument to pass through to the callable
    # - A filter to match events to so the callable is only invoked when
    #   appropriate
    #
    #eventFilter = {'Shotgun_Task_Change': ['sg_status_list']}
    eventFilter = None
    # Retrieve config values
    my_name = reg.getName()
    cfg = reg.getConfig()
    if not cfg :
        raise ConfigError( "No config file found")
    reg.logger.debug( "Loading config for %s" % reg.getName() )
    settings = {}
    keys = [ 'sgEntity', 'script_key', 'script_name']
    for k in keys :
        settings[k] = cfg.get( my_name, k )
        reg.logger.debug( "Using %s %s" % ( k, settings[k] ) )
    # Register all callbacks related to our custom entity
    events = [ r'Shotgun_%s_New', r'Shotgun_%s_Change', r'Shotgun_%s_New', r'Shotgun_%s_Retirement', r'Shotgun_%s_Revival']
    eventFilter = {}
    for e in events :
        eventFilter[ e % settings['sgEntity'] ] = ['sg_status_list', 'retirement_date' ] # retirement_date
    reg.logger.debug( "Registering %s" % eventFilter)
    reg.registerCallback( settings['script_name'], settings['script_key'], logArgs, eventFilter, settings )

    # Get a list of all the existing plugins from Shotgun
    sgHandle = sg.Shotgun( reg.getEngine().config.getShotgunURL(), settings['script_name'], settings['script_key'] )
    plugins = sgHandle.find( settings['sgEntity'], [], ['sg_script_path'] )
    reg.logger.debug( "Plugins : %s", plugins )
    for p in plugins :
        if p['sg_script_path'] and p['sg_script_path']['local_path'] :
            reg.logger.info( "Loading %s", p['sg_script_path']['name'] )
            _loadPlugin( reg.getEngine(), p['sg_script_path'] and p['sg_script_path']['local_path'])
    # Set the logging level for this particular plugin. Let error and above
    # messages through but block info and lower. This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    #reg.logger.setLevel(logging.ERROR)

def _loadPlugin( engine, path ) :
    """
        Load the given plugin in the given Engine
        @param engine : The engine to load the plugin into
        @param path : Full path to the plugin Python script
    """
    # Check that everything looks right
    if not os.path.isfile(path) :
        raise ValueError( "%s is not a valid file path" % path )
    ( dir, file ) = os.path.split( path )
    # Check if we already have a plugin collection covering the directory path
    for pc in engine._pluginCollections :
        if pc.path == dir :
            break
    else :
        # Need to create a new plugin collection
        engine._pluginCollections.append( PluginCollection(engine, dir) )
        pc = engine._pluginCollections[-1]

    if file not in pc._plugins : # Plugin is not already loaded
        pc[file] = Plugin(pc._engine, os.path.join(dir, file))
        pc[file].load()
    return pc[file]


def logArgs(sg, logger, event, args):
    """
    A callback that logs its arguments.

    @param sg: Shotgun instance.
    @param logger: A preconfigured Python logging.Logger object
    @param event: A Shotgun event.
    @param args: The args passed in at the registerCallback call.
    """
    logger.info("%s" % str(event))
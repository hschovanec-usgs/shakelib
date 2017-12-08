#!/usr/bin/env python

# stdlib imports
import os.path
import sys
import io
import json
import numpy as np
import datetime as dt
import time
import datetime
import tempfile
import pytest

from shakelib.utils.containers import ShakeMapInputContainer
from shakelib.utils.containers import ShakeMapOutputContainer
from shakelib.rupture.point_rupture import PointRupture

from mapio.geodict import GeoDict
from mapio.grid2d import Grid2D

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, '..', '..'))
sys.path.insert(0, shakedir)


def dict_equal(d1, d2):
    s1 = sorted(set(d1.keys()))
    s2 = sorted(set(d2.keys()))
    return s1 == s2


def test_input_container():
    f,datafile = tempfile.mkstemp()
    os.close(f)
    try:
        config = {'alliance': 'chaotic neutral',
                  'race': 'Elf',
                  'armor': 5,
                  'class': 'Warrior',
                  'intelligence': 10}
        rupturefile = os.path.join(homedir, 'container_data', 
                                   'Barkaetal02_fault.txt')
        event_text = """<?xml version="1.0" encoding="US-ASCII" standalone="yes"?>
    <earthquake id="2008ryan" lat="30.9858" lon="103.3639" mag="7.9" year="2008"
    month="05" day="12" hour="06" minute="28" second="01" timezone="GMT"
    depth="19.0" locstring="EASTERN SICHUAN, CHINA" created="1211173621" productcode="us2008ryan"
    otime="1210573681" type="" />"""
        eventfile = io.StringIO(event_text)
        datafiles = [os.path.join(
            homedir, 'container_data/northridge_stations_dat.xml')]

        timestamp = datetime.datetime.utcnow().strftime('%FT%TZ')
        originator = 'us'
        version = 1
        history = {'history': [[timestamp, originator, version]]}

        container = ShakeMapInputContainer.createFromInput(datafile,
                                                           config,
                                                           eventfile,
                                                           history,
                                                           datafiles=datafiles,
                                                           rupturefile=rupturefile)
        cfile = container.getFileName()
        assert datafile == cfile
        config = container.getConfig()
        station = container.getStationList()
        rupture = container.getRuptureObject()
        history = container.getVersionHistory()
        container.close()

        container2 = ShakeMapInputContainer.load(datafile)
        config2 = container2.getConfig()
        station2 = container2.getStationList()  # noqa
        rupture2 = container2.getRuptureObject()  # noqa
        history2 = container2.getVersionHistory()  # noqa

        assert dict_equal(config, config2)
        df1 = station.getStationDictionary(instrumented=False)
        df2 = station2.getStationDictionary(instrumented=False)
        assert dict_equal(df1, df2)
        df1 = station.getStationDictionary(instrumented=True)
        df2 = station2.getStationDictionary(instrumented=True)
        assert dict_equal(df1, df2)
        assert history['history'][-1][0] == history['history'][-1][0]
        assert history['history'][-1][1] == history['history'][-1][1]
        assert history['history'][-1][2] == history['history'][-1][2]

        container2.close()

        eventfile.seek(0)
        container3 = ShakeMapInputContainer.createFromInput(datafile, 
                                                            config, 
                                                            eventfile, 
                                                            {})
        try:
            #this should fail, because we haven't set any station data yet
            station = container3.getStationList()
        except AttributeError:
            assert 1 == 1
        rupture = container3.getRuptureObject()
        history = container3.getVersionHistory()
        assert len(history) == 0
        assert isinstance(rupture, PointRupture)

        container3.setStationData(datafiles)

        #
        # Test the getStationDict() and setStationDict() functions with
        # some dummy data
        #
        config = {'alliance': 'chaotic neutral',
                  'race': 'Elf',
                  'armor': 5,
                  'class': 'Warrior',
                  'intelligence': 10}
        with pytest.raises(AttributeError):
            junk = container3.getStationDict()
        with pytest.raises(TypeError):
            container3.setStationDict(None)
        container3.setStationDict(config)
        config2 = container3.getStationDict()
        assert dict_equal(config, config2)

    except:
        assert 1==2
    finally:
        os.remove(datafile)


def test_output_container():
    geodict = GeoDict.createDictFromBox(-118.5,-114.5,32.1,36.7,0.01,0.02)
    nrows,ncols = geodict.ny,geodict.nx

    #create MMI mean data for maximum component
    mean_mmi_maximum_data = np.random.rand(nrows,ncols)
    mean_mmi_maximum_metadata = {'name':'Gandalf',
                                 'color':'white',
                                 'powers':'magic'}
    mean_mmi_maximum_grid = Grid2D(mean_mmi_maximum_data,geodict)

    #create MMI std data for maximum component
    std_mmi_maximum_data = mean_mmi_maximum_data/10
    std_mmi_maximum_metadata = {'name':'Legolas',
                                'color':'green',
                                'powers':'good hair'}
    std_mmi_maximum_grid = Grid2D(std_mmi_maximum_data,geodict)

    #create MMI mean data for rotd50 component
    mean_mmi_rotd50_data = np.random.rand(nrows,ncols)
    mean_mmi_rotd50_metadata = {'name':'Gimli',
                                 'color':'brown',
                                 'powers':'axing'}
    mean_mmi_rotd50_grid = Grid2D(mean_mmi_rotd50_data,geodict)

    #create MMI std data for rotd50 component
    std_mmi_rotd50_data = mean_mmi_rotd50_data/10
    std_mmi_rotd50_metadata = {'name':'Aragorn',
                                'color':'white',
                                'powers':'scruffiness'}
    std_mmi_rotd50_grid = Grid2D(std_mmi_rotd50_data,geodict)

    #create PGA mean data for maximum component
    mean_pga_maximum_data = np.random.rand(nrows,ncols)
    mean_pga_maximum_metadata = {'name':'Pippin',
                                 'color':'purple',
                                 'powers':'rashness'}
    mean_pga_maximum_grid = Grid2D(mean_pga_maximum_data,geodict)

    #create PGA std data for maximum component
    std_pga_maximum_data = mean_pga_maximum_data/10
    std_pga_maximum_metadata = {'name':'Merry',
                                'color':'grey',
                                'powers':'hunger'}
    std_pga_maximum_grid = Grid2D(std_pga_maximum_data,geodict)
    
    f,datafile = tempfile.mkstemp()
    os.close(f)
    try:
        container = ShakeMapOutputContainer.create(datafile)
        container.setIMT('mmi',
                         mean_mmi_maximum_grid,mean_mmi_maximum_metadata,
                         std_mmi_maximum_grid,std_mmi_maximum_metadata,
                         component='maximum')
        container.setIMT('mmi',
                         mean_mmi_rotd50_grid,mean_mmi_rotd50_metadata,
                         std_mmi_rotd50_grid,std_mmi_rotd50_metadata,
                         component='rotd50')
        container.setIMT('pga',
                         mean_pga_maximum_grid,mean_pga_maximum_metadata,
                         std_pga_maximum_grid,std_pga_maximum_metadata,
                         component='maximum')

        #get the maximum MMI imt data
        mmi_max_dict = container.getIMT('mmi',component='maximum')
        np.testing.assert_array_equal(mmi_max_dict['mean'].getData(),
                                      mean_mmi_maximum_data)
        np.testing.assert_array_equal(mmi_max_dict['std'].getData(),
                                      std_mmi_maximum_data)
        assert mmi_max_dict['mean_metadata'] == mean_mmi_maximum_metadata
        assert mmi_max_dict['std_metadata'] == std_mmi_maximum_metadata

        #get the rotd50 MMI imt data
        mmi_rot_dict = container.getIMT('mmi',component='rotd50')
        np.testing.assert_array_equal(mmi_rot_dict['mean'].getData(),
                                      mean_mmi_rotd50_data)
        np.testing.assert_array_equal(mmi_rot_dict['std'].getData(),
                                      std_mmi_rotd50_data)
        assert mmi_rot_dict['mean_metadata'] == mean_mmi_rotd50_metadata
        assert mmi_rot_dict['std_metadata'] == std_mmi_rotd50_metadata

        #get list of maximum imts
        max_imts = container.getIMTs(component='maximum')
        assert sorted(max_imts) == ['mmi','pga']

        #get list of components for mmi
        mmi_comps = container.getComponents('mmi')
        assert sorted(mmi_comps) == ['maximum','rotd50']

        
                             
    except Exception as e:
        raise(e)
    finally:
        os.remove(datafile)
    
    
    
        
if __name__ == '__main__':
    test_input_container()
    test_output_container()

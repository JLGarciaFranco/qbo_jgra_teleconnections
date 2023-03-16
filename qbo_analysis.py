import iris
import datetime
import pandas as pd
import seasonal
from .other_tools import *
def deseason_level(series,tvec):
	seasons,trend=seasonal.fit_seasons(np.squeeze(np.asarray(series)),period=12)
	print('seasoned 12')
	seasonsi,trendi=seasonal.fit_seasons(np.squeeze(np.asarray(series)))
	print('seasons')
	print(seasons)
	if seasons is None:
		miniseries=series[0:1000]
		datos=miniseries.groupby('time.month').mean(dim='time')
		nuevosdatos=np.zeros(len(series))
		seriesval=series.values
		for ij,val in enumerate(series):
			dataval=datos[datos.month==val.time.dt.month]
			nuevosdatos[ij]=seriesval[ij]-dataval
		return nuevosdatos
	else:
		adjusted=seasonal.adjust_seasons(np.squeeze(series),seasons=seasons)
		print(adjusted)
		try:
			residual=adjusted#-trend
			return residual
		except:
			return series

def qboIndex(filename,typo,llevel,write=None,outputf=None):
	if type(filename)==str:
		cube=iris.load_cube(filename)
	elif type(filename)==list:
		cubes=iris.load(filename)
		for ij,cube in enumerate(cubes):
			cubes[ij].attributes={}
		cube=cubes.concatenate()
		cube=cubes.concatenate_cube()
	else:
		cube=filename
	print(typo,np.min(cube.data))
	latconstraint=iris.Constraint(latitude=lambda cell: -3<cell<3)
	time=cube.coord('time')#

	if typo=='reanalysis':
		plconstraint=iris.Constraint(pressure_level=lambda cell: 9<cell<90)
		pcoord='pressure_level'
		levconstraint=iris.Constraint(pressure_level=lambda cell: cell==level)
		
	elif typo=='cmip':
		pcoord='air_pressure'
		plevels=cube.coord(pcoord).points
		if np.max(plevels)>10000:
			fact = 100
		else:
			fact =1
		plconstraint=iris.Constraint(air_pressure=lambda cell: 9*fact<cell<90*fact)

	elif typo=='suites' or typo =='qboi':
		plconstraint=iris.Constraint(pressure=lambda cell: 9<cell<90)
		fact =1
		pcoord='pressure'
		levconstraint=iris.Constraint(pressure=lambda cell: cell==level)
	plevels=cube.coord(pcoord).points
	cube=cube.extract(plconstraint)
	xrr=xr.DataArray.from_iris(cube)	
	plevels=cube.coord(pcoord).points
	print(plevels)
	if len(cube.shape)>2:
		cube=cube.extract(latconstraint)
		cube=cube.collapsed('latitude',iris.analysis.MEAN)
		cube=cube.collapsed('longitude',iris.analysis.MEAN)
	if write and type(llevel)==list:
		for lev in llevel:	
			print(lev,fact)
			if typo=='reanalysis':
				levconstraint=iris.Constraint(pressure_level=lambda cell: cell==lev)
			elif typo=='cmip':
				levconstraint=iris.Constraint(air_pressure=lambda cell: cell==lev*fact)
			elif typo=='suites' or typo == 'qboi':
				levconstraint=iris.Constraint(pressure=lambda cell: cell==lev)
			cubi=cube.extract(levconstraint)#iris.Constraint(air_pressure=lambda cell: cell==7000))
			print('deseasonalizing',lev)
			cubi.data=deseason_level(xr.DataArray.from_iris(cubi),xrr.time)
			print('saving')
			os.system('rm '+outputf+str(lev)+'.txt')
			qbofile=open(outputf+str(lev)+'.txt','a')
			df=pd.DataFrame(cubi.data,index=xrr.time.values)
			for ij,dt in enumerate(df.values):
				date=str(df.index[ij])
				qbofile.write(date+','+str(float(dt))+'\n')
			qbofile.close()
	else:
		return cube


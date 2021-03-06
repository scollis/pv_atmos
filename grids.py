#!/usr/bin/python
# Filename: grids.py
#
# Code by Martin Jucker, distributed under an MIT License
# Any publication benefitting from this piece of code should cite
# Jucker, M 2014. Scientific Visualisation of Atmospheric Data with ParaView.
# Journal of Open Research Software 2(1):e4, DOI: http://dx.doi.org/10.5334/jors.al
#
# Python interface for ParaView (www.paraview.org). Provides means to add axes in Cartesian or spherical coordinates.

##### needed modules: paraview.simple, math #########################
from paraview.simple import *
from math import log10

##------------ General functions for adding/extracting and labeling planes ---------------------

# do the math for logarithmic coordinates - no coordinate conversion
def Lin2Log(x, ratio=1.0, basis=1e3):
    """Convert linear coordinate to logarithmic coordinate value
        
        x     -- the coordinate value to convert
        ratio -- the multiplicative factor after log10
        basis -- basis to normalize argument to logarithm (ie defines origin).
        """
    import math
    level = abs(log10(x/basis))*ratio
    return level

# adjust aspect ratio of bounding box vector
def BoundAspectRatio(bounds, ratios, logCoord=[2], basis=[1e3]):
    """Adjust aspect ratio of bounding box (axes).
        
        Inputs are:
        bounds     -- Physical bounds of 2D or 3D axes [Xmin,Xmax,Ymin,Ymax,Zmin,Zmax]
        ratios     -- Corrections to actually plotted axes
        logCoord   -- Which of the coordinates is in log scale [array]. Default is 3rd (pressure)
        basis      -- basis to normalize logarithmic coordinate(s). If len==1, applied to all logCoord, otherwise must be same length as logCoord
        Outputs are:
        Xmin,Xmax,Ymin,Ymax,Zmin,Zmax of axes
        """
    boundsIn=bounds[:]
    #first, deal with log scale coordinates
    for pp in range(len(logCoord)):
        if len(boundsIn) > 2*logCoord[pp]:
            if len(basis) > 0 :
                bas = basis[pp]
            else:
                bas = basis[0]
            boundsIn[logCoord[pp]*2  ] = Lin2Log(bounds[logCoord[pp]*2  ],1.0,bas)
            boundsIn[logCoord[pp]*2+1] = Lin2Log(bounds[logCoord[pp]*2+1],1.0,bas)
    #then apply aspect ratios
    Xmin   = boundsIn[0]*ratios[0]
    Xmax  = boundsIn[1]*ratios[0]
    Ymin   = boundsIn[2]*ratios[1]
    Ymax    = boundsIn[3]*ratios[1]
    if len(bounds) == 6 :
        Zmin = boundsIn[4]*ratios[2]
        Zmax = boundsIn[5]*ratios[2]
        return Xmin,Xmax,Ymin,Ymax,Zmin,Zmax
    else:
        return Xmin,Xmax,Ymin,Ymax

# add a plane perpendicular to a given dimension
def AddGridPlane(dim, x, bounds=[0.0,360.0,-90.0,90.0], ratios=[1,1,1], logCoord=[2], basis=[1e3], data=0, src=GetActiveSource(), AxisColor=[0,0,0], AxisWidth=1.0):
    """Extract or add a plane, i.e. perpendicular to dimension dim.
        
        Either to add a grid line, or a data plane perpendicular to a given dimension.
        if data ==1, extracts a horizontal plane from data, else adds an empty plane for grid only
        
        INPUTS:
            dim     -- index of the dimension to work on. 0,1,2
            x       -- physical value at which plane should be extracted/created. In original coordinates, not converted (unknown) coordinates
            bounds  -- extremities of grid box [Xmin,Xmax,Ymin,Ymax[,Zmin,Zmax]]
            ratios  -- aspect ratios of axes
            logCoord-- index/indices of coordinates to be treated logarithmically
            basis   -- basis to normalize logarithmic coordinate(s). If len==1, applied to all logCoord, otherwise must be same length as logCoord
            data    -- whether (1) or not (0) plane extracts data
            src     -- filter in pipeline to attach to
            AxisColor -- color of lines in RGB
            AxisWidth -- width of lines
        OUTPUTS:
            Plane1   -- New plane in the pipeline, either containing data or not
        """
    if dim in logCoord :
        level = Lin2Log(x,ratios[dim],basis[logCoord.index(dim)])
    else:
        level = x*ratios[dim]

    if len(bounds) == 4 :
        (Xmin,Xmax,Ymin,Ymax) = BoundAspectRatio(bounds, ratios, logCoord, basis)
    else:
        (Xmin,Xmax,Ymin,Ymax,Zmin,Zmax) = BoundAspectRatio(bounds, ratios, logCoord, basis)
    # make sure we place the plane in the right direction
    if dim == 0:
        origin  = [level, Ymax, Zmin]
        origin1 = [level, Ymin, Zmin]
        origin2 = [level, Ymax, Zmax]
    elif dim == 1:
        origin  = [Xmin, level, Zmin]
        origin1 = [Xmax, level, Zmin]
        origin2 = [Xmin, level, Zmax]
    else:
        origin  = [Xmin, Ymin, level]
        origin1 = [Xmax, Ymin, level]
        origin2 = [Xmin, Ymax, level]
    normal = [0.0, 0.0, 0.0]
    normal[dim] = 1.0
    if data == 1 : #extract plane from data
        Plane1 = Slice(src)
        Plane1.SliceType.Origin = origin
        Plane1.SliceType.Normal = normal
        Plane1Rep = Show(Plane1)
        Plane1Rep.Representation = 'Surface'
    else: #create new plane otherwise
        Plane1 = Plane()
        Plane1.Origin = origin
        Plane1.Point1 = origin1 #Origin -> Point1 defines x-axis of plane
        Plane1.Point2 = origin2 #Origin -> Point2 defines y-axis of plane
        Plane1Rep = Show(Plane1)
        Plane1Rep.Representation = 'Outline'
        Plane1Rep.AmbientColor = AxisColor
        Plane1Rep.LineWidth = AxisWidth
    return Plane1

# add a label at a given place along a dimension, outside the domain
def AddGridLabel(dim, x, LabelSize=5.0, bounds=[0.0,360,-90.0,90.0], ratios=[1,1,1], logCoord=[2], basis=[1e3], AxisColor=[0,0,0]):
    """Adds a label at a given position along a given dimension, outside the domain (e.g. for axes labeling).
        
        The label text is the same as the value of x.
        
        INPUTS:
            x         -- Position and name of label
            LabelSize -- Size of the label text
            bounds    -- bounds of axes: label is positioned just outside these bounds [Xmin,Xmax,Ymin,Ymax[,Zmin,Zmax]]
            ratios    -- aspect ratios of axes
            logCoord  -- index/indices of coordinates to be treated logarithmically
            basis     -- basis to normalize logarithmic coordinate(s). If len==1, applied to all logCoord, otherwise must be same length as logCoord
            AxisColor -- color of lines in RGB
        OUTPUTS:
            Label       -- The label itself
            Trans{1..4} -- Transforms to position the labels. 2 for x and y, 4 for z
    """
    if dim in logCoord :
        level = Lin2Log(x,ratios[dim],basis[logCoord.index(dim)])
    else:
        level = x*ratios[dim]
    
    if len(bounds) == 4 :
        (Xmin,Xmax ,Ymin,Ymax) = BoundAspectRatio(bounds, ratios, logCoord, basis)
    else:
        (Xmin,Xmax ,Ymin,Ymax,Zmin ,Zmax) = BoundAspectRatio(bounds, ratios, logCoord, basis)
    LabelScale = [abs(LabelSize), abs(LabelSize), abs(LabelSize)]
    Label = a3DText(Text=str(x))
    
    percentOff = 0.02
    # the z labels are shown at all four courners
    # the x and y labels are shown only twice, at the bottom on each side
    if dim == 2:
        shiftY = percentOff*(Ymax-Ymin)
        shiftX = percentOff*(Xmax-Xmin)
        translate1 = [ Xmax         , Ymax + shiftY, level ]
        rotate1    = [ 90.0, 90.0,  0.0 ]
        translate2 = [ Xmax + shiftX, Ymin         , level ]
        rotate2    = [ 90.0,  0.0,  0.0 ]
        translate3 = [ Xmin - shiftX, Ymax         , level ]
        rotate3    = [ 90.0,180.0,  0.0]
        translate4 = [ Xmin         , Ymin - shiftY, level ]
        rotate4    = [ 90.0,-90.0,  0.0 ]
    else:
        Z = Zmin  - LabelSize*1.5
        if dim == 1:
            if x < 0.0:
                shiftY = LabelSize*1.5
            elif x > 0.0:
                shiftY = LabelSize
            else:
                shiftY = LabelSize*0.5
            translate1 = [ Xmax, level - shiftY, Z ]
            rotate1    = [ 90.0, 90.0,  0.0 ]
            translate2 = [ Xmin, level + shiftY, Z ]
            rotate2    = [ 90.0,-90.0,  0.0 ]
        else:
            if x < 100.0:
                shiftX = LabelSize*1.0
            else:
                shiftX = LabelSize*1.5
            translate1 = [ level - shiftX, Ymin, Z ]
            rotate1    = [ 90.0,  0.0,  0.0 ]
            translate2 = [ level + shiftX, Ymax, Z ]
            rotate2    = [ 90.0,180.0,  0.0 ]
    #now apply those transformations and rotations to get the labels into the corners
    Trans1 = Transform()
    Trans1.Transform.Translate = translate1
    Trans1.Transform.Rotate = rotate1
    Trans1.Transform.Scale = LabelScale
    Trans1.SMProxy.InvokeEvent('UserEvent','HideWidget') #don't show box
    Rep = GetDisplayProperties()
    Rep.Representation = 'Surface'
    Rep.DiffuseColor = AxisColor
    Rep.BackfaceRepresentation = 'Cull Backface' #hidden from behind
    Trans2 = Transform(Label)
    Trans2.Transform.Translate = translate2
    Trans2.Transform.Rotate = rotate2
    Trans2.Transform.Scale = LabelScale
    Trans2.SMProxy.InvokeEvent('UserEvent','HideWidget') #don't show box
    Rep = GetDisplayProperties()
    Rep.Representation = 'Surface'
    Rep.DiffuseColor = AxisColor
    Rep.BackfaceRepresentation = 'Cull Backface'
    if dim == 2:
        Trans3 = Transform(Label)
        Trans3.Transform.Translate = translate3
        Trans3.Transform.Rotate = rotate3
        Trans3.Transform.Scale = LabelScale
        Trans3.SMProxy.InvokeEvent('UserEvent','HideWidget') #don't show box
        Rep = GetDisplayProperties()
        Rep.Representation = 'Surface'
        Rep.DiffuseColor = AxisColor
        Rep.BackfaceRepresentation = 'Cull Backface'
        Trans4 = Transform(Label)
        Trans4.Transform.Translate = translate4
        Trans4.Transform.Rotate = rotate4
        Trans4.Transform.Scale = LabelScale
        Trans4.SMProxy.InvokeEvent('UserEvent','HideWidget') #don't show box
        Rep = GetDisplayProperties()
        Rep.Representation = 'Surface'
        Rep.DiffuseColor = AxisColor
        Rep.BackfaceRepresentation = 'Cull Backface'
        return Label,Trans1,Trans2,Trans3,Trans4
    else:
        return Label,Trans1,Trans2

# move generic label with given position and rotation
def AddAxisLabel(Labl,Trans,Rot, AxisColor=[0,0,0], LabelSize=5.0,):
    """Move a generic label.

    Modifies Labl according to the transformations Trans, Rot, LabelSize:
    Labl  -- input object, usually a3DText
    Trans -- translation vector [dx,dy,dz]
    Rot   -- rotation vector [rx,ry,rz]
    LabelSize -- Size of the label text
    AxisColor -- text color
    Adds a Transform filter to the pipeline
    """
    LabelScale = [LabelSize, LabelSize, LabelSize]
    TransLab = Transform(Labl)
    TransLab.Transform.Translate = Trans
    TransLab.Transform.Rotate = Rot
    TransLab.Transform.Scale = LabelScale
    TransLab.SMProxy.InvokeEvent('UserEvent','HideWidget')
    Rep = GetDisplayProperties()
    Rep.Representation = 'Surface'
    Rep.DiffuseColor = AxisColor
    Rep.BackfaceRepresentation = 'Cull Backface'
    return TransLab

# Add vertical labels in spherical coordinates
def SphericalLabels(radius=1, ratios=[1,1,1], logCoord=[2], basis=[1e3], shellValues=[100,10,1], labelPosition=[170, 10], labelSize=1.0):
    """Label vertical surface(s) that has(have) been extracted in spherical geometry (shell).

    radius   -- radius of sphere with r(basis)=radius
    ratios   -- aspect ratios of axes before converting to sphere
    logCoord -- index/indices of coordinates to be treated logarithmically
    basis    -- basis to normalize logarithmic coordinate(s). If len==1, applied to all logCoord, otherwise must be same length as logCoord
    shellValues -- vector of values to be labelled, in original units (before ratios conversion)
    labelPosition -- the position in [longitude,latitude] on the sphere
    labelSize -- multiplicative factor for size of the labels
    Adds the label text, a Transform and a Calculator filter to the pipeline
        """
    if 2 in logCoord :
        if len(basis) > 0:
            bas = basis[logCoord.index(2)]
        else:
            bas = basis[0]
    for p in range(len(shellValues)):
        ps = shellValues[p]
        if 2 in logCoord :
            if ps >= bas :
                fac = 1.01
            else:
                fac = 0.99
            labelRadius = radius + Lin2Log(fac*ps,ratios[2],bas)
        else:
            labelRadius = radius + 1.01*ps*ratios[2]
        txt=a3DText()
        txt.Text = str(abs(ps))
        rep=Show(txt);rep.Visibility=0
        RenameSource('Text'+str(ps)+'[Z]',txt)
        Transform1=Transform(txt)
        Transform1.Transform="Transform"
        Transform1.Transform.Rotate    =[0.0,0.0,90.0]
        if abs(ps) >= 1:
            Transform1.Transform.Scale     =[3.0*labelSize,3.0*labelSize, 1.0*labelSize]
        else:
            Transform1.Transform.Scale     =[2.0*labelSize,2.0*labelSize, 1.0*labelSize]
        Transform1.Transform.Translate =[labelPosition[0], labelPosition[1], labelRadius]
        rep=Show(Transform1);rep.Visibility=0
        Text2Sphere = Cart2Spherical(0,Transform1)
        Text_disp=Show()
        Text_disp.DiffuseColor = [0.0, 0.0, 0.0]
        Text_disp.Opacity=0.5

# add a water mark to denote authorship of plot
def WaterMark(waterMark, markRadius=1, markPosition=[250, 10], markSize=1.0):
    """Add a water mark on the sphere as signature.

    waterMark  -- text to project onto the sphere
    markRadius -- radius of water mark, already converted from physical units
    markPosition -- position of water mark in [longitude, latitude] on the sphere
    markSize   -- size of the water mark label
    Adds a a3DText, Transform, and a Calculator filter to the pipeline
    """
    txt=a3DText()
    txt.Text = waterMark
    rep=Show();rep.Visibility=0
    RenameSource('WaterMark',txt)
    Transform2=Transform()
    Transform2.Transform="Transform"
    Transform2.Transform.Scale     =[2.0*markSize,2.0*markSize, 1.0*markSize]
    Transform2.Transform.Translate =[markPosition[0], markPosition[1], markRadius]
    rep=Show(Transform2);rep.Visibility=0
    Mark2Sphere = Cart2Spherical(0,Transform2)
    Text_disp=Show()
    Text_disp.DiffuseColor = [0.0, 0.0, 0.0]
    Text_disp.Opacity=0.1

## Combine some of the above to create a suite of atmospheric shells.
#    this replaces the grid in spherical geometry
#
# For independence of grids.py and basic.py, need to duplicate Cart2Spherical here
def Cart2Spherical(radius=1.0, src=GetActiveSource()):
    """Convert Cartesian to spherical coordinates.
        
        Assumes X coordinate is longitude, Y coordinate latitude, Z coordinate vertical.
        Adds Calculator filter to the pipeline.
        radius -- radius of the sphere, where coordZ = basis
        src    -- filter in pipeline to attach to
        """
    from math import pi
    calc=Calculator(src)
    strRad = str(radius)
    strPi = str(pi)[0:7]
    try:
        calc.Function = 'iHat*('+strRad+'+coordsZ)*cos(coordsY*'+strPi+'/180)*cos(coordsX*'+strPi+'/180) + jHat*('+strRad+'+coordsZ)*cos(coordsY*'+strPi+'/180)*sin(coordsX*'+strPi+'/180) + kHat*('+strRad+'+coordsZ)*sin(coordsY*'+strPi+'/180)'
    except:
        calc.Function = 'iHat*'+strRad+'*cos(coordsY*'+strPi+'/180)*cos(coordsX*'+strPi+'/180) + jHat*'+strRad+'*cos(coordsY*'+strPi+'/180)*sin(coordsX*'+strPi+'/180) + kHat*'+strRad+'*sin(coordsY*'+strPi+'/180)'
    calc.CoordinateResults = 1
    RenameSource('Cart2Spherical',calc)
    return calc
#
def SphericalShells(radius=1, ratios=[1,1,1], logCoord=[2], basis=[1e3], src=GetActiveSource(), shellValues=[100,10,1], labels=1, labelPosition=[170, 10], waterMark='none', markPosition=[250, 10], labelSize=1.0):
    """Add spherical shells as grid to spherical geometry, or to visualize specific pressure levels.

    Adds as many shells as there are shellValues.
    
    Combines AddGridPlane, SphericalLabels, and WaterMark to create a grid in spherical coordinates.
    radius        -- radius of sphere with r(basis)=radius
    ratios        -- aspect ratios of axes before converting to sphere
    logCoord      -- index/indices of coordinates to be treated logarithmically
    basis         -- basis to normalize logarithmic coordinate(s). If len==1, applied to all logCoord, otherwise must be same length as logCoord
    src           -- filter in pipeline to attach to
    shellValues   -- vector of values to be labelled, in original units (hPa,km)
    labels        -- add labels (>0) or not (0)
    labelPosition -- the position in [longitude,latitude] on the sphere
    waterMark     -- string with text for water mark, or 'none'
    markPosition  -- position of water mark in [longitude, latitude] on the sphere
    labelSize     -- multiplicative factor for size of labels and water mark
    Adds a Plane, two Calculators, a a3DText, and a Transform to the pipeline.
    If a water mark is included, adds an additional a3DText, Transform, and a Calculator filter to the pipeline.
    Returns a list of all pressure planes for further treatment.
    """
    Planes=[]
    for ps in shellValues:
        TropoSlice = AddGridPlane(2, ps, ratios=ratios, logCoord=logCoord, basis=basis, data=1, src=src)
        rep=Show(TropoSlice);rep.Visibility=0
        RenameSource(str(ps)+'[Z]',TropoSlice)
        Cart2Sphere = Cart2Spherical(radius,TropoSlice)
        TropoSlice_disp=Show()
        TropoSlice_disp.Opacity=0.1
        Planes.append(Cart2Sphere)

        if labels>0:
            SphericalLabels(radius, ratios, logCoord, basis, [ps], labelPosition, labelSize)
    
    # add watermark
    if waterMark != 'none':
        if 2 in logCoord :
            if len(basis) > 0:
                bas = basis[logCoord.index(2)]
            else:
                bas = basis[0]
            labelRadius = Lin2Log(min(shellValues),ratios[2],bas)
        else:
            labelRadius = radius + shellValues[-1]*ratios[2]
        WaterMark(waterMark, labelRadius, markPosition, labelSize)
    return Planes

###### add full set of grids and lables in rectangular geometry ############################
def AddGrid(xlevels=[0,90,180,270], ylevels=[-60,-30,0,30,60], zlevels=[100,10,1,0.1], bounds=[0.0,360.0,-90.0,90.0,1e3,0.1], ratios=[1,1,1], logCoord=[2], basis=[1e3], AxisNames=["lon","lat","pressure [hPa]"], AxisColor=[0,0,0], AxisWidth=2.0,LabelSize=5.0):
    """Add a full grid with grid lines and labels.
        
        Adds as many X,Y,Z grid lines as needed. This function adds a lot of objects and filters to the pipeline, and should probably only be used once the visualization itself is finished. This function can be called even if there is no data loaded.

        INPUTS:
            xlevels   -- vector with X grid positions
            ylevels   -- vector with Y grid positions
            zlevels   -- vector with Z grid levels
            bounds    -- grid bounds
            ratios    -- axes ratios
            basis     -- basis (surface) pressure
            AxisNames -- names of x,y,z axis
            AxisColor -- color of lines in RGB
            AxisWidth -- width of lines
            LabelSize -- Size of the label text
        """
    (Xmin,Xmax,Ymin,Ymax,Zmin,Zmax) = BoundAspectRatio(bounds, ratios, logCoord, basis)
    absLsz = abs(LabelSize)
    #Z grid
    if len(zlevels) > 0:
        for z in zlevels:
            PlaneTmp = AddGridPlane(2, z, bounds[0:4], ratios, logCoord, basis, AxisColor=AxisColor, AxisWidth=AxisWidth)
            RenameSource("Plane"+str(z),PlaneTmp)
            if abs(LabelSize) > 0.0 :
                (label,transa,transb,transc,transd) = AddGridLabel(2, z, absLsz, bounds[0:4], ratios, logCoord, basis, AxisColor)
                RenameSource("Label"+str(z),label)
                Show(transa)
                Show(transb)
                Show(transc)
                Show(transd)
        
        #Z axis label
        if LabelSize > 0.0 :
            BoxH = Zmax - Zmin 
            LabelTmp = a3DText(Text=AxisNames[2])
            RenameSource("ZLabel",LabelTmp)
            LabelPushFac = len(str(max(max(zlevels),abs(min(zlevels)))))+2
            if max(zlevels) < abs(min(zlevels)):
                LabelPushFac += 2
            Transx = [
                      Xmax , Xmax +LabelPushFac*absLsz, Xmin, Xmin-LabelPushFac*absLsz ]
            Transy = [Ymax+LabelPushFac*absLsz, Ymin, Ymin-LabelPushFac*absLsz, Ymax ]
            Rotx = [ 180.0,   0.0, 180.0, 180.0 ]
            Roty = [  90.0, -90.0,  90.0,  90.0 ]
            Rotz = [   0.0,  90.0, 180.0,  90.0 ]
            for i in range(len(Transx)):
                Trans = [ Transx[i], Transy[i], Zmin + BoxH*0.5 -4.0*absLsz ]
                Rot = [ Rotx[i], Roty[i], Rotz[i] ]
                TransPres = AddAxisLabel(LabelTmp, Trans, Rot, AxisColor, absLsz)
                
    # for other coordinate labels
    Z = Zmin  - absLsz*3.0
    #Y grid
    if len(ylevels) > 0:
        for y in ylevels:
            PlaneTmp = AddGridPlane(1, y, bounds, ratios, logCoord, basis, AxisColor=AxisColor, AxisWidth=AxisWidth)
            RenameSource("Plane"+str(y),PlaneTmp)
            if abs(LabelSize) > 0.0 :
                (label,transa,transb) = AddGridLabel(1, y, absLsz, bounds, ratios, logCoord, basis, AxisColor)
                RenameSource("Label"+str(y),label)
                Show(transa)
                Show(transb)
        #Y axis label
        if LabelSize > 0.0 :
            LabelTmp = a3DText(Text=AxisNames[1])
            RenameSource("YLabel",LabelTmp)
            midY = 0.5*(Ymax+Ymin)
            Trans = [Xmax , midY-2.5*absLsz, Z]
            Rot = [ 90.0, 90.0, 0.0 ]
            TransLat = AddAxisLabel(LabelTmp, Trans, Rot, AxisColor, absLsz)
            
            Trans = [Xmin, midY+2.5*absLsz, Z]
            Rot = [ 90.0,-90.0, 0.0 ]
            TransLat = AddAxisLabel(LabelTmp, Trans, Rot, AxisColor, absLsz)

    #X grid
    if len(xlevels) > 0 :
        for x in xlevels:
            PlaneTmp = AddGridPlane(0, x, bounds, ratios, logCoord, basis, AxisColor=AxisColor, AxisWidth=AxisWidth)
            RenameSource("Plane"+str(x)+"[X]",PlaneTmp)
            if abs(LabelSize) > 0.0 :
                (label,transa,transb) = AddGridLabel(0, x, absLsz, bounds, ratios, logCoord, basis, AxisColor)
                Show(transa)
                Show(transb)

        #X axis label
        if LabelSize > 0.0 :
            LabelTmp = a3DText(Text=AxisNames[0])
            RenameSource("XLabel",LabelTmp)
            Trans = [0.5*(Xmin+Xmax )-3.0*absLsz, Ymin, Z]
            Rot = [ 90.0,   0.0, 0.0 ]
            TransLon = AddAxisLabel(LabelTmp, Trans, Rot, AxisColor, absLsz)
            
            Trans = [0.5*(Xmin+Xmax)+3.0*absLsz, Ymax, Z]
            Rot = [ 90.0, 180.0, 0.0 ]
            TransLon = AddAxisLabel(LabelTmp, Trans, Rot, AxisColor, absLsz)






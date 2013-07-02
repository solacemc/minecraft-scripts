# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from pymclevel import TAG_List
from pymclevel import TAG_Byte
from pymclevel import TAG_Int
from pymclevel import TAG_Compound
from pymclevel import TAG_Short
from pymclevel import TAG_Double
from pymclevel import TAG_String
from pymclevel import TAG_Int_Array
from pymclevel import TAG_Float
from pymclevel import TAG_Long
import math

displayName = "Structure Spawner v2"

inputs = (
	("Slowness Factor", (1, 1, 100)),
	("Spawners Relative Position:", "label"),
	("dx", 5),
	("dy", 0),
	("dz", 0),
	("Create Spawner", True),
	("Create Deleter", True),
	("Create Grass", True),
)

NonSolids = [6, 8, 9, 10, 11, 26, 27, 28, 30, 31, 32, 36, 37, 38, 39, 40, 44, 50, 51, 54, 55, 59, 63, 64, 66, 68, 69, 70, 71, 72, 75, 76, 77, 78, 81, 83, 85, 92, 93, 94, 96, 104, 105, 106, 107, 111, 113, 115, 118, 119, 120, 122, 126, 127, 130, 131, 132, 139, 140, 141, 142, 143, 144, 146, 147, 148, 149, 150, 151, 157]

########## Fast data access ##########
from pymclevel import ChunkNotPresent
GlobalChunkCache = {}
GlobalLevel = None

def getChunk(x, z):
	global GlobalChunkCache
	global GlobalLevel
	chunkCoords = (x>>4, z>>4)
	if chunkCoords not in GlobalChunkCache:
		try:
			GlobalChunkCache[chunkCoords] = GlobalLevel.getChunk(x>>4, z>>4)
		except ChunkNotPresent:
			return None

	return GlobalChunkCache[chunkCoords]

def blockAt(x, y, z):
	chunk = getChunk(x, z)
	if chunk == None:
		return 0
	return chunk.Blocks[x%16][z%16][y]

def dataAt(x, y, z):
	chunk = getChunk(x, z)
	if chunk == None:
		return 0
	return chunk.Data[x%16][z%16][y]

def tileEntityAt(x, y, z):
	chunk = getChunk(x, z)
	if chunk == None:
		return 0
	return chunk.tileEntityAt(x, y, z)

########## End fast data access ##########

def perform(level, box, options):
	global GlobalLevel
	GlobalLevel = level

	if options["Create Spawner"]:
		spawns = buildStructureSpawners(box)
		spawns = spawns + deleteGlassSpawners(box)
		createSpawners(level, box, options, spawns, -3, "Spawn")

	if options["Create Deleter"]:
		spawns = deleteStructureSpawners(box)
		createSpawners(level, box, options, spawns, 3, "Delete")

	if options["Create Grass"]:
		blocks = gatherBoxContents(box)
		print 'blocks: %s' & blocks

def gatherBoxContents(box):
	return [12, 23, 32]

def createSpawners(level, box, options, spawns, sdx, text):
	# Find redstone/spawner coordinates
	dx = options["dx"]
	dy = options["dy"]
	dz = options["dz"]

	if dx == 0:
		rsx = (box.maxx + box.minx) / 2
	if dy == 0:
		rsy = (box.maxy + box.miny) / 2
	if dz == 0:
		rsz = (box.maxz + box.minz) / 2

	if dx < 0:
		rsx = box.minx + dx - 5
	if dy < 0:
		rsy = box.miny + dy - 2
	if dz < 0:
		rsz = box.minz + dz - 5

	if dx > 0:
		rsx = box.maxx + dx + 5
	if dy > 0:
		rsy = box.maxy + dy + 5
	if dz > 0:
		rsz = box.maxz + dz + 2

	rsx = rsx + sdx

	# Create Spawner Carts
	(_, _, _, _, maxDelay, _) = max(spawns, key=lambda(spos, sblock, sdata, stileEntity, sdelay, stime): sdelay)
	prevDelayCart = None
	for delay in xrange(maxDelay, -1, -1):
		prevCart = None
		for (spos, sblock, sdata, stileEntity, sdelay, stime) in spawns:
			if sdelay == delay:
				sand = fallingSand((spos, sblock, sdata, stileEntity, stime))
				prevCart = minecartSpawner((rsx+2, rsy, rsz), prevCart, sand, False)

		prevDelayCart = minecartSpawner((rsx+2, rsy, rsz), prevDelayCart, prevCart, True)

	cart = minecartSpawner((rsx+2, rsy, rsz), None, prevDelayCart, False)
	mainCart = minecartSpawner((rsx, rsy, rsz), cart, None, False)
	mainCart["MinSpawnDelay"] = TAG_Short(32000)
	mainCart["MaxSpawnDelay"] = TAG_Short(32000)

	# Create Spawner Tile Entity and Bogus Cart
	level.setBlockAt(rsx, rsy-1, rsz, 52)
	spawner = spawnerTileEntity((rsx, rsy-1, rsz), 1, 1, 1, mainCart)
	chunk = getChunk(rsx, rsz)
	chunk.TileEntities.append(spawner)
	bogusCart = minecartSpawner((rsx, rsy, rsz), None, None, False)
	bogusCart["MinSpawnDelay"] = TAG_Short(32000)
	bogusCart["MaxSpawnDelay"] = TAG_Short(32000)
	bogusCart["Delay"] = TAG_Short(32000)
	chunk.Entities.append(bogusCart)
	chunk.dirty = True

	# Create scaffolding
	level.setBlockAt(rsx+2, rsy, rsz, 11) #lava
	level.setBlockAt(rsx+3, rsy, rsz, 20) #glass
	level.setBlockAt(rsx+2, rsy, rsz+1, 20) #glass
	level.setBlockAt(rsx+2, rsy, rsz-1, 20) #glass
	level.setBlockAt(rsx+2, rsy-1, rsz, 20) #glass
	level.setBlockAt(rsx+1, rsy, rsz, 23) #dispenser
	level.setBlockDataAt(rsx+1, rsy, rsz, 4) #dispenser direction
	chunk = getChunk(rsx+1, rsz)
	chunk.TileEntities.append(lavaDispenser(rsx+1, rsy, rsz))
	chunk.dirty = True
	level.setBlockAt(rsx+1, rsy, rsz-1, 1) #stone
	level.setBlockAt(rsx+1, rsy, rsz+1, 1) #stone
	level.setBlockAt(rsx+1, rsy+1, rsz-1, 55), #redstone dust
	level.setBlockAt(rsx+1, rsy+1, rsz+1, 55), #redstone dust
	level.setBlockAt(rsx+1, rsy+1, rsz, 93) #repeater
	level.setBlockDataAt(rsx+1, rsy+1, rsz, 12) #repeater delay

	# Create monostable circuit
	level.setBlockAt(rsx+1, rsy+1, rsz+3, 1) #stone
	level.setBlockAt(rsx+1, rsy+1, rsz+5, 1) #stone
	level.setBlockAt(rsx+1, rsy+2, rsz+4, 1) #stone
	level.setBlockAt(rsx+1, rsy+3, rsz+5, 1) #stone
	level.setBlockAt(rsx+1, rsy+1, rsz+2, 75) #torch off
	level.setBlockDataAt(rsx+1, rsy+1, rsz+2, 4) #torch on wall
	level.setBlockAt(rsx+1, rsy+1, rsz+4, 93) #repeater
	level.setBlockDataAt(rsx+1, rsy+1, rsz+4, 8) #repeater delay
	level.setBlockAt(rsx+1, rsy, rsz+4, 1) #stone
	level.setBlockAt(rsx+1, rsy+2, rsz+5, 76) #torch on
	level.setBlockDataAt(rsx+1, rsy+2, rsz+5, 5) #torch on floor
	level.setBlockAt(rsx+1, rsy+2, rsz+3, 55) #redstone dust on
	level.setBlockDataAt(rsx+1, rsy+2, rsz+3, 14) #redstone dust on
	level.setBlockAt(rsx+1, rsy+3, rsz+4, 55) #redstone dust on
	level.setBlockDataAt(rsx+1, rsy+3, rsz+4, 15) #redstone dust on
	level.setBlockAt(rsx, rsy+1, rsz+5, 143) #button
	level.setBlockDataAt(rsx, rsy+1, rsz+5, 2) #button on wall
	level.setBlockAt(rsx, rsy+2, rsz+4, 68) #sign
	level.setBlockDataAt(rsx, rsy+2, rsz+4, 4) #sign on wall
	chunk = getChunk(rsx, rsz+4)
	chunk.dirty = True
	width = box.maxx-box.minx
	height = box.maxy-box.miny
	depth = box.maxz-box.minz
	sign = signTileEntity(rsx, rsy+2, rsz+4, text, "{0}x{1}x{2}".format(width, height, depth), "{0} ticks".format(maxDelay+9), "{0} Sand".format(len(spawns)))
	chunk.TileEntities.append(sign)

def buildStructureSpawners(box):
	spawns = []
	for x in xrange(box.minx, box.maxx):
		for z in xrange(box.minz, box.maxz):
			needsSupport = False
			for y in xrange(box.maxy-1, box.miny-1, -1):
				block = blockAt(x, y, z)
				if needsSupport and (block == 0 or block in NonSolids):
					block = 20
				if block != 0:
					spawns.append(((x+0.5, y+0.51, z+0.5), block, dataAt(x, y, z), tileEntityAt(x, y, z), y-box.miny+1, 1))
					needsSupport = True

	return spawns

def deleteGlassSpawners(box):
	spawns = []

	for x in xrange(box.minx, box.maxx):
		for z in xrange(box.minz, box.maxz):
			currentDelay = 5
			currentDrop = 0
			needsSupport = False
			for y in xrange(box.maxy-1, box.miny-2, -1):
				block = blockAt(x, y, z)
				if block != 0:
					if currentDrop > 0:
						if block in NonSolids:
							spawns.append(((x+0.5, y+0.75, z+0.5), 20, 0, None, currentDelay+y-box.miny, 0))
						else:
							spawns.append(((x+0.5, y+0.75, z+0.5), block, dataAt(x, y, z), None, currentDelay+y-box.miny, 0))
						spawns.append(((x+0.5, y+0.25, z+0.5), 44, 0, None, currentDelay+y-box.miny, 1))
						currentDelay = currentDelay + int(1.7*currentDrop) + 10
						spawns.append(((x+0.5, y+0.75, z+0.5), 44, 0, None, currentDelay + y-box.miny - 4, 0))
						spawns.append(((x+0.5, y+0.25, z+0.5), block, dataAt(x, y, z), tileEntityAt(x, y, z), currentDelay + y-box.miny - 4, 1))
					elif block in NonSolids:
						spawns.append(((x+0.5, y+0.75, z+0.5), 20, 0, None, currentDelay+y-box.miny, 0))
						spawns.append(((x+0.5, y+0.25, z+0.5), block, dataAt(x, y, z), tileEntityAt(x, y, z), currentDelay+y-box.miny, 1))
						currentDelay = currentDelay + 4
					else:
						currentDelay = 5
					needsSupport = True
					currentDrop = 0
				elif needsSupport:
					spawns.append(((x+0.5, y+0.5, z+0.5), 20, 0, None, currentDelay+y-box.miny, 0))
					currentDrop = currentDrop + 1

	return spawns

def deleteStructureSpawners(box):
	spawns = []

	for x in xrange(box.minx, box.maxx):
		for z in xrange(box.minz, box.maxz):
			currentDelay = 2
			currentDrop = 0
			needsSupport = False
			for y in xrange(box.maxy-1, box.miny-2, -1):
				block = blockAt(x, y, z)
				if y == box.miny-1:
					if currentDrop > 0:
						spawns.append(((x+0.5, y+0.75, z+0.5), block, dataAt(x, y, z), None, currentDelay+y-box.miny, 0))
						spawns.append(((x+0.5, y+0.25, z+0.5), 44, 0, None, currentDelay+y-box.miny, 1))
						currentDelay = currentDelay + int(1.7*currentDrop) + 10
						spawns.append(((x+0.5, y+0.75, z+0.5), 44, 0, None, currentDelay-4, 0))
						spawns.append(((x+0.5, y+0.25, z+0.5), block, dataAt(x, y, z), None, currentDelay-4, 1))
					break

				if block != 0:
					spawns.append(((x+0.5, y+0.5, z+0.5), block, dataAt(x, y, z), None, currentDelay+y-box.miny, 0))
					needsSupport = True

				if needsSupport:
					currentDrop = currentDrop + 1

	return spawns

def spawnerTileEntity((x, y, z), maxEntities, spawnRange, loopTicks, entity):
	mobSpawner = TAG_Compound()
	mobSpawner["id"] = TAG_String(u'MobSpawner')
	mobSpawner["MinSpawnDelay"] = TAG_Short(loopTicks)
	mobSpawner["MaxSpawnDelay"] = TAG_Short(loopTicks)
	mobSpawner["Delay"] = TAG_Short(0)
	mobSpawner["SpawnCount"] = TAG_Short(1)
	mobSpawner["RequiredPlayerRange"] = TAG_Short(1000)
	mobSpawner["MaxNearbyEntities"] = TAG_Short(maxEntities)
	mobSpawner["SpawnRange"] = TAG_Short(spawnRange)
	mobSpawner["SpawnData"] = entity
	mobSpawner["EntityId"] = TAG_String(u'MinecartSpawner')
	mobSpawner["x"] = TAG_Int(x)
	mobSpawner["y"] = TAG_Int(y)
	mobSpawner["z"] = TAG_Int(z)

	return mobSpawner

def minecartSpawner((cx, cy, cz), spawn1, spawn2, initialDelay=True):
	spawnerCart = TAG_Compound()
	spawnerCart["id"] = TAG_String(u'MinecartSpawner')
	spawnerCart["Items"] = TAG_List()
	motion = TAG_List()
	motion.append(TAG_Double(0.0))
	motion.append(TAG_Double(0.0))
	motion.append(TAG_Double(0.0))
	spawnerCart["Motion"] = motion
	spawnerCart["OnGround"] = TAG_Byte(0)
	spawnerCart["Type"] = TAG_Int(0)

	if initialDelay:
		# 1 tick delay before first spawn, 1 tick before second
		spawnerCart["MinSpawnDelay"] = TAG_Short(1)
		spawnerCart["MaxSpawnDelay"] = TAG_Short(1)
		spawnerCart["Delay"] = TAG_Short(2)
	else:
		# instantaneous first spawn, 2 ticks before second
		spawnerCart["MinSpawnDelay"] = TAG_Short(2)
		spawnerCart["MaxSpawnDelay"] = TAG_Short(2)
		spawnerCart["Delay"] = TAG_Short(0)

	spawnerCart["Dimension"] = TAG_Int(0)
	spawnerCart["Air"] = TAG_Short(300)
	spawnerCart["SpawnCount"] = TAG_Short(1)
	pos = TAG_List()
	pos.append(TAG_Double(cx + 0.5))
	pos.append(TAG_Double(cy + 0.35))
	pos.append(TAG_Double(cz + 0.5))
	spawnerCart["Pos"] = pos
	spawnerCart["PortalCooldown"] = TAG_Int(0)
	spawnerCart["RequiredPlayerRange"] = TAG_Short(32000)
	spawnerCart["Fire"] = TAG_Short(-1)
	spawnerCart["MaxNearbyEntities"] = TAG_Short(32000)
	spawnerCart["FallDistance"] = TAG_Float(0.0)
	rotation = TAG_List()
	rotation.append(TAG_Float(0.0))
	rotation.append(TAG_Float(0.0))
	spawnerCart["Rotation"] = rotation
	spawnerCart["SpawnRange"] = TAG_Short(1)
	spawnerCart["Invulnerable"] = TAG_Byte(0)

	if spawn1 == None:
		bs = bogusSpawn(cx, cz)
		spawnerCart["SpawnData"] = bs
		spawnerCart["EntityId"] = TAG_String(bs["id"].value)
	else:
		spawnerCart["SpawnData"] = spawn1
		spawnerCart["EntityId"] = TAG_String(spawn1["id"].value)

	spawnPotentials = TAG_List()
	spawnPotential = TAG_Compound()
	if spawn2 == None:
		spawnPotential["Properties"] = bogusSpawn(cx, cz)
	else:
		spawnPotential["Properties"] = spawn2

	spawnPotential["Weight"] = TAG_Int(1)
	spawnPotential["Type"] = TAG_String(spawnPotential["Properties"]["id"].value)
	spawnPotentials.append(spawnPotential)
	spawnerCart["SpawnPotentials"] = spawnPotentials

	return spawnerCart

def bogusSpawn(cx, cz):
	properties = TAG_Compound()
	properties["id"] = TAG_String(u'Item')
	properties["Age"] = TAG_Short(19)
	motion = TAG_List()
	motion.append(TAG_Double(0))
	motion.append(TAG_Double(0))
	motion.append(TAG_Double(0))
	properties["Motion"] = motion
	properties["OnGround"] = TAG_Byte(1)
	properties["Health"] = TAG_Short(5)
	properties["Dimension"] = TAG_Int(0)
	properties["Air"] = TAG_Short(300)
	pos = TAG_List()
	pos.append(TAG_Double(cx))
	pos.append(TAG_Double(-100))
	pos.append(TAG_Double(cz))
	properties["Pos"] = pos
	properties["PortalCooldown"] = TAG_Int(0)
	item = TAG_Compound()
	item["id"] = TAG_Short(24)
	item["Damage"] = TAG_Short(0)
	item["Count"] = TAG_Byte(1)
	properties["Item"] = item
	properties["Fire"] = TAG_Short(-1)
	properties["FallDistance"] = TAG_Float(0.0)
	rotation = TAG_List()
	rotation.append(TAG_Float(0))
	rotation.append(TAG_Float(0))
	properties["Rotation"] = rotation
	properties["Invulnerable"] = TAG_Byte(0)

	return properties

def fallingSand(((x, y, z), tile, data, tileEntity, time)):
	fallingSand = TAG_Compound()
	fallingSand["id"] = TAG_String(u'FallingSand')
	motion = TAG_List()
	motion.append(TAG_Double(0.0))
	motion.append(TAG_Double(0.0))
	motion.append(TAG_Double(0.0))
	fallingSand["Motion"] = motion
	fallingSand["OnGround"] = TAG_Byte(0)
	fallingSand["DropItem"] = TAG_Byte(0)
	fallingSand["Dimension"] = TAG_Int(0)
	fallingSand["Air"] = TAG_Short(300)
	pos = TAG_List()
	pos.append(TAG_Double(x))
	pos.append(TAG_Double(y))
	pos.append(TAG_Double(z))
	fallingSand["Pos"] = pos
	fallingSand["Data"] = TAG_Byte(data)
	fallingSand["TileID"] = TAG_Int(tile)
	fallingSand["Time"] = TAG_Byte(time)
	fallingSand["Fire"] = TAG_Short(-1)
	fallingSand["FallDistance"] = TAG_Float(0.0)
	if tileEntity != None:
		fallingSand["TileEntityData"] = tileEntity
	rotation = TAG_List()
	rotation.append(TAG_Float(0.0))
	rotation.append(TAG_Float(0.0))
	fallingSand["Rotation"] = rotation

	return fallingSand

def lavaDispenser(x, y, z):
	trap = TAG_Compound()
	trap["id"] = TAG_String(u'Trap')
	items = TAG_List()
	item = TAG_Compound()
	item["id"] = TAG_Short(327)
	item["Damage"] = TAG_Short(0)
	item["Count"] = TAG_Byte(1)
	item["Slot"] = TAG_Byte(4)
	items.append(item)
	trap["Items"] = items
	trap["x"] = TAG_Int(x)
	trap["y"] = TAG_Int(y)
	trap["z"] = TAG_Int(z)

	return trap

def signTileEntity(x, y, z, text1, text2, text3, text4):
	sign = TAG_Compound()
	sign["id"] = TAG_String(u'Sign')
	sign["Text1"] = TAG_String(text1)
	sign["Text2"] = TAG_String(text2)
	sign["Text3"] = TAG_String(text3)
	sign["Text4"] = TAG_String(text4)
	sign["x"] = TAG_Int(x)
	sign["y"] = TAG_Int(y)
	sign["z"] = TAG_Int(z)

	return sign

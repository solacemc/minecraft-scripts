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

displayName = "Grass Box"

inputs = (
	("Create Grass", True),
)

def perform(level, box, options):
	if options["Create Grass"]:
		makeGrass(level, box)

def makeGrass(level, box):
	blocks = []

	for x in xrange(box.minx, box.maxx):
		for z in xrange(box.minz, box.maxz):
			y = box.maxy
			while y >= box.miny:
				level.setBlockAt(x, y, z, level.materials.Grass.ID)
				y = y - 1
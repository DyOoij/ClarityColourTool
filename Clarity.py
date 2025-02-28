import pygame
import subprocess

pygame.init()

#Main global and loop variables
CurrentlyRunning = True
clock = pygame.time.Clock()


#Display settings and UI initialisation, the WIDTH and HEIGHT double as the amount of pixels in that direction
WIDTH = 1530
HEIGHT = 380
HUEBARHEIGHT = 40
GRABARHEIGHT = 40
GSCBARHEIGHT = 30
MTDBARHEIGHT = 30
SEPARATEBAR = 5

DisplaySurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Clarity Colour Tool")

font = pygame.font.SysFont("Lucida Console", 20)


#Spectrum settings
TotalSaturates = WIDTH
HueHexCode = '0xff0000'

#HueHexBox settings
HUEHEXBOXHEIGHT = 70
HUEHEXBOXWIDTH = int(WIDTH / 4)
GraHexCode = '0xff0000'

#Gradient settings
GradientSpread = int(WIDTH/2)
GRAHEXBOXWIDTH = int(WIDTH/2)

#Grayscale settings
GreyScaleScaler = 6
GscHexCode = '0xffffff'
TempGreyedHex = ['0x000000']

#Muted gradient settings
MutedScaleScaler = 6
MtdHexCode = '0xff0000'

def CreateSpectrum():
    #Creates a list of all possible saturated RGB tuples 
    #The amount depends on the initial total colours (min 6, max 1530)
    #Due to the Scaler loop dividing by 6, any multiple of 6 rounded down will add
    #    an extra "band" of 6 hues
    
    ColourStepper = int(1530/TotalSaturates)
    RGB = [255,0,0] #Changing this value also requires a change in logic flow down the line, so keep it like this
    RGBTuples = []
    Location = 1
    PosOrNeg = 1
  
    for Scaler in range(6): #There are 3 colours (RGB) and two directions (scale up or down), so 6 regions to
                            #iterate through in total
        for step in range(int(TotalSaturates/6)):
            ShiftingColour = RGB[Location]
            RGBTuples.append(RGB.copy()) #.copy() is required here due to list mutibility
            RGB[Location] = ShiftingColour + ColourStepper * PosOrNeg

        PosOrNeg *= -1
        Location -= 1
        if Location == -1:
            Location = 2    
    return RGBTuples
            
def ConvertToHex(RGBTuples):
    #Converts RGB tuples into 0x format hex codes
    HexCodes = []
    for Tuple in RGBTuples:
        HexCodes.append("0x" + hex(Tuple[0])[2:].zfill(2) + hex(Tuple[1])[2:].zfill(2) + hex(Tuple[2])[2:].zfill(2))
    return HexCodes

       
def SpectrumToScreen(HexCodes):
    Iterator = 0
    #Iterates over the Grid and prints pixels to the PyGame window
    for PixelColour in HexCodes:
        #Determine the location and apply the size modifier              
        pygame.draw.rect(DisplaySurface,
                         pygame.Color(PixelColour),
                         (Iterator, 0, 1, HUEBARHEIGHT))
        Iterator += 1

def HexToScreen(Left, Top, SizeX, SizeY, Colour):
    #Draws a region of the currently hovered saturated hue to the screen
    pygame.draw.rect(DisplaySurface,
                     pygame.Color(Colour),
                     (Left, Top, SizeX, SizeY))
                                
def CreateGradient():
    #Takes the current saturated hue and scales the brightness 100% up and down
    #returns a list of RGB tuples
    
    GradientLight = []
    GradientTotal  = []
    
    #This just splits the hex into 00 to FF bits
    red = int(HueHexCode[2:4], 16)
    gre = int(HueHexCode[4:6], 16)
    blu = int(HueHexCode[6:],  16)
    
    #The general idea here is to have the white to colour to black incremental change normalised over a range (think percentages)
    #This range is indicated by GradientSpread
    #Each RGB value gets normalised over this range (220 and 117 to 225 don't increment at the same rate)
    #in either a lighter step (stepl) or darker step (stepd), then the RGB value in question gets adjusted accordingly
    
    rstepl = CalculateGradientLightStep(red)
    gstepl = CalculateGradientLightStep(gre)
    bstepl = CalculateGradientLightStep(blu)
    
    for percentage in range(GradientSpread + 1):
        GradientLight.append([int(red+rstepl*percentage), int(gre+gstepl*percentage), int(blu+bstepl*percentage)])
        
    for GradientLightEntry in reversed(GradientLight):
        #The light step gets reversed so the colour flows from white > colour > black as opposed to colour > white | colour > black
        GradientTotal.append(GradientLightEntry)
        
    rstepd = CalculateGradientDarkStep(red)
    gstepd = CalculateGradientDarkStep(gre)
    bstepd = CalculateGradientDarkStep(blu)
    
    for percentage in range(GradientSpread):
        GradientTotal.append([int(red+rstepd*percentage), int(gre+gstepd*percentage), int(blu+bstepd*percentage)])
    
    return GradientTotal

def GradientToScreen(HexCodes):
    Iterator = 0
    #Iterates over the Grid and prints pixels to the PyGame window
    for PixelColour in HexCodes:
        #Determine the location and apply the size modifier               
        pygame.draw.rect(DisplaySurface,
                         pygame.Color(PixelColour),
                         (Iterator, HUEBARHEIGHT + HUEHEXBOXHEIGHT + 2 * SEPARATEBAR, 1, GRABARHEIGHT))
        Iterator += 1

def CreateGreyScale():
    GreyScaleValues = []
    for RGBStep in range(int(WIDTH/GreyScaleScaler) + 1):
        GreyScaleValues.insert(0, (3 * hex(RGBStep)[2:].zfill(2)))
    return GreyScaleValues

def GreyScaleToScreen(GreyScaleList):
    Iterator = 0
    #Iterates over the GrayScaleList to print a white to black bar for muted colour selection 
    for PixelColour in GreyScaleList:
        #Determine the location and apply the size modifier
        pygame.draw.rect(DisplaySurface,
                         pygame.Color('#' + PixelColour),
                         (Iterator, HUEBARHEIGHT + GRABARHEIGHT + 2 * HUEHEXBOXHEIGHT + 4 * SEPARATEBAR, GreyScaleScaler, GSCBARHEIGHT))
        Iterator += GreyScaleScaler
        
def CreateMutedGradient(ColourHex): 
    #Takes the current gradient hue and scales the brightness 100% up and down
    #returns a list of RGB tuples
    
    TempGreyedHex[0] = ColourHex
    
    MutedGradient = []
        
    #This just splits the hex into 00 to FF bits
    red = int(ColourHex[2:4], 16)
    gre = int(ColourHex[4:6], 16)
    blu = int(ColourHex[6:],  16)
    
    GreyValue = int(GscHexCode[2:4], 16)

    
    redstep = (GreyValue - red)/255
    grestep = (GreyValue - gre)/255
    blustep = (GreyValue - blu)/255
       
    for GradientStrip in range(256):
        #There are only 256 different possible muted states (00 to ff)
        MutedGradient.insert(0, [int(red+redstep*GradientStrip), int(gre+grestep*GradientStrip), int(blu+blustep*GradientStrip)])
    
    return MutedGradient
        
def MutedGradientToScreen(MutedGradientList):
    Iterator = 0
    #Iterates over the Grid and prints pixels to the PyGame window
    for PixelColour in MutedGradientList:
        #Determine the location and apply the size modifier               
        pygame.draw.rect(DisplaySurface,
                         pygame.Color(PixelColour),
                         (Iterator, HUEBARHEIGHT + GRABARHEIGHT+ 2 * HUEHEXBOXHEIGHT + 5 * SEPARATEBAR + GSCBARHEIGHT, MutedScaleScaler, MTDBARHEIGHT))
        Iterator += MutedScaleScaler

    

def DetermineComplementHex(HueHexCode):
    #What a fucking mess lmao, but returns the complementary colour hex
    return ('#' + hex(0xffffff - int(HueHexCode,16))[2:].zfill(6))

def DetermineTriadicHexes(HueHexCode):
    #Returns the triadic colour by shifting the string bits around
    #No math here, head empty, just hacksaw work
    HexString = HueHexCode[2:]
    
    #upshift
    UpHex =  HexString[4:] + HexString[0:2] + HexString[2:4]
    #downshift
    DownHex = HexString[2:] + HexString[:2]
    return ['#' + UpHex, '#' + DownHex]
    
    
    

    

def CalculateGradientLightStep(ColourValue):
    #normalise changes in RGB values in CreateGradient()
    return (255-ColourValue)/GradientSpread

def CalculateGradientDarkStep(ColourValue):
    #normalise changes in RGB values in CreateGradient()
    return (0-ColourValue)/GradientSpread

def MousePositioner():
    #Floor dividing the mouse position by PIXELMULTUPLIER basically scales down the screen's resolution
    MouseX = (pygame.mouse.get_pos()[0])//1
    MouseY = (pygame.mouse.get_pos()[1])//1
    return(MouseX, MouseY)


def CopyToClipboard(Text):
    return
    cmd='echo ' + Text.strip()+'|clip'
    return subprocess.check_call(cmd, shell=True) 





HexCodeList = ConvertToHex(CreateSpectrum())
SpectrumToScreen(HexCodeList)

GradientList = ConvertToHex(CreateGradient())
GradientToScreen(GradientList)

GreyScaleList = CreateGreyScale()
GreyScaleToScreen(GreyScaleList)

MutedGradientList = ConvertToHex(CreateMutedGradient(HueHexCode))
MutedGradientToScreen(MutedGradientList)


while CurrentlyRunning == True:
    
    #initialise and update the the following colour boxes
    #selected saturated colour
    HexToScreen(0, (HUEBARHEIGHT + SEPARATEBAR ), HUEHEXBOXWIDTH, HUEHEXBOXHEIGHT, HueHexCode)
    DisplaySurface.blit(font.render("Main: " + HueHexCode[2:], True, pygame.Color('#000000')), (0, (HUEBARHEIGHT + SEPARATEBAR),0,0))
    #selected complementary colour
    HexToScreen(HUEHEXBOXWIDTH + SEPARATEBAR, (HUEBARHEIGHT + SEPARATEBAR), HUEHEXBOXWIDTH, HUEHEXBOXHEIGHT, DetermineComplementHex(HueHexCode))
    DisplaySurface.blit(font.render("Complement: " +DetermineComplementHex(HueHexCode)[1:], True, pygame.Color('#000000')), (HUEHEXBOXWIDTH + SEPARATEBAR, (HUEBARHEIGHT + SEPARATEBAR ) ,0,0))
    #selected triadic colour 1
    HexToScreen(HUEHEXBOXWIDTH * 2 + SEPARATEBAR * 2, (HUEBARHEIGHT + SEPARATEBAR), HUEHEXBOXWIDTH, HUEHEXBOXHEIGHT, DetermineTriadicHexes(HueHexCode)[0])
    DisplaySurface.blit(font.render("Minor Triad: " +DetermineTriadicHexes(HueHexCode)[0][1:], True, pygame.Color('#000000')), ((HUEHEXBOXWIDTH + SEPARATEBAR) * 2,(HUEBARHEIGHT + SEPARATEBAR),0,0))
    #selected triadic colour 2
    HexToScreen(HUEHEXBOXWIDTH * 3 + SEPARATEBAR * 3, (HUEBARHEIGHT + SEPARATEBAR), HUEHEXBOXWIDTH, HUEHEXBOXHEIGHT, DetermineTriadicHexes(HueHexCode)[1])
    DisplaySurface.blit(font.render("Major Triad: " +DetermineTriadicHexes(HueHexCode)[1][1:], True, pygame.Color('#000000')), ((HUEHEXBOXWIDTH + SEPARATEBAR) * 3,(HUEBARHEIGHT + SEPARATEBAR),0,0))
    
    #Gradient bar
    GradientToScreen(GradientList)
    
    #Row 2 Hex Boxes 1-2
    HexToScreen(0, (HUEBARHEIGHT + GRABARHEIGHT + HUEHEXBOXHEIGHT + 3 * SEPARATEBAR ), GRAHEXBOXWIDTH + SEPARATEBAR, HUEHEXBOXHEIGHT, GraHexCode)
    DisplaySurface.blit(font.render("Gradient: " + GraHexCode[2:], True, pygame.Color(DetermineComplementHex(GraHexCode))), (0,(HUEBARHEIGHT + GRABARHEIGHT + HUEHEXBOXHEIGHT + SEPARATEBAR * 3),0,0))
    HexToScreen((GRAHEXBOXWIDTH + SEPARATEBAR * 2), (HUEBARHEIGHT + GRABARHEIGHT + HUEHEXBOXHEIGHT + 3 * SEPARATEBAR), GRAHEXBOXWIDTH , HUEHEXBOXHEIGHT, DetermineComplementHex(GraHexCode))
    DisplaySurface.blit(font.render("Gradient Complement: " + DetermineComplementHex(GraHexCode)[1:], True, pygame.Color(GraHexCode)), (GRAHEXBOXWIDTH + SEPARATEBAR * 2,(HUEBARHEIGHT + GRABARHEIGHT + HUEHEXBOXHEIGHT + SEPARATEBAR * 3),0,0))

    #Grayscale bar
    GreyScaleToScreen(GreyScaleList)
    DisplaySurface.blit(font.render("Greyscale: " + GscHexCode.replace('0x',''), True, pygame.Color('#000000')), (0,(HUEBARHEIGHT + GRABARHEIGHT + 2 * HUEHEXBOXHEIGHT + SEPARATEBAR * 5),0,0))
    
    #Muted colour bar
    MutedGradientToScreen(MutedGradientList)
    
    #Last row of Hex boxes
    #selected muted colour
    HexToScreen(0, (HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + MTDBARHEIGHT  + HUEHEXBOXHEIGHT * 2 + SEPARATEBAR * 6), HUEHEXBOXWIDTH, HUEHEXBOXHEIGHT, MtdHexCode)
    DisplaySurface.blit(font.render("Muted: " + MtdHexCode[2:], True, pygame.Color('#000000')), (0, (HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + MTDBARHEIGHT  + HUEHEXBOXHEIGHT * 2 + SEPARATEBAR * 6),0,0))
    #selected complementary colour
    HexToScreen(HUEHEXBOXWIDTH + SEPARATEBAR, (HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + MTDBARHEIGHT  + HUEHEXBOXHEIGHT * 2 + SEPARATEBAR * 6), HUEHEXBOXWIDTH, HUEHEXBOXHEIGHT, DetermineComplementHex(MtdHexCode))
    DisplaySurface.blit(font.render("Complement: " +DetermineComplementHex(MtdHexCode)[1:], True, pygame.Color('#000000')), (HUEHEXBOXWIDTH + SEPARATEBAR, (HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + MTDBARHEIGHT  + HUEHEXBOXHEIGHT * 2 + SEPARATEBAR * 6) ,0,0))
    #selected triadic colour 1
    HexToScreen(HUEHEXBOXWIDTH * 2 + SEPARATEBAR * 2, (HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + MTDBARHEIGHT  + HUEHEXBOXHEIGHT * 2 + SEPARATEBAR * 6), HUEHEXBOXWIDTH, HUEHEXBOXHEIGHT, DetermineTriadicHexes(MtdHexCode)[0])
    DisplaySurface.blit(font.render("Minor Triad: " +DetermineTriadicHexes(MtdHexCode)[0][1:], True, pygame.Color('#000000')), ((HUEHEXBOXWIDTH + SEPARATEBAR) * 2,(HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + MTDBARHEIGHT  + HUEHEXBOXHEIGHT * 2 + SEPARATEBAR * 6),0,0))
    #selected triadic colour 2
    HexToScreen(HUEHEXBOXWIDTH * 3 + SEPARATEBAR * 3, (HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + MTDBARHEIGHT  + HUEHEXBOXHEIGHT * 2 + SEPARATEBAR * 6), HUEHEXBOXWIDTH, HUEHEXBOXHEIGHT, DetermineTriadicHexes(MtdHexCode)[1])
    DisplaySurface.blit(font.render("Major Triad: " +DetermineTriadicHexes(MtdHexCode)[1][1:], True, pygame.Color('#000000')), ((HUEHEXBOXWIDTH + SEPARATEBAR) * 3,(HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + MTDBARHEIGHT  + HUEHEXBOXHEIGHT * 2 + SEPARATEBAR * 6),0,0))

   
    
    
    clock.tick(99)
    pygame.display.flip()
      
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            CurrentlyRunning = False
            
    if pygame.mouse.get_pressed()[0] == True:
        
        
        MouseX = MousePositioner()[0]
        MouseY = MousePositioner()[1]
        
        if MouseX >= 0 and MouseX < WIDTH:
            if MouseY >= 0 and MouseY < HUEBARHEIGHT:
                #This is the hue spectrum region
                HueHexCode = HexCodeList[MouseX]
                GradientList = ConvertToHex(CreateGradient())
                GradientToScreen(GradientList)
                DetermineComplementHex(HueHexCode)
                DetermineTriadicHexes(HueHexCode)
                MutedGradientList = ConvertToHex(CreateMutedGradient(HueHexCode))
               
                
            
                
                
            elif MouseY >= HUEBARHEIGHT + 2 * SEPARATEBAR + HUEHEXBOXHEIGHT and MouseY < HUEBARHEIGHT + HUEHEXBOXHEIGHT + GRABARHEIGHT + 2 * SEPARATEBAR:
                #This is the gradient spectrum region
                MutedGradientList = ConvertToHex(CreateMutedGradient(GraHexCode))
                GraHexCode = GradientList[MouseX]
                
            elif MouseY >= HUEBARHEIGHT + SEPARATEBAR and MouseY < HUEBARHEIGHT + HUEHEXBOXHEIGHT + SEPARATEBAR:
                #This is the top row of hue hexes
                if MouseX < WIDTH/4:
                    #saturate
                    CopyToClipboard(HueHexCode[2:])
                elif MouseX < WIDTH/2:
                    #complement
                    CopyToClipboard(DetermineComplementHex(HueHexCode)[1:])
                elif MouseX < WIDTH/(4/3):
                    #triad 1
                    CopyToClipboard(DetermineTriadicHexes(HueHexCode)[0][1:])
                elif MouseX < WIDTH/1:
                    #triad 2
                    CopyToClipboard(DetermineTriadicHexes(HueHexCode)[1][1:])
                    
            elif MouseY >= HUEBARHEIGHT + GRABARHEIGHT + HUEHEXBOXHEIGHT + 3 * SEPARATEBAR  and MouseY < HUEBARHEIGHT + GRABARHEIGHT + 2 * HUEHEXBOXHEIGHT + 3 * SEPARATEBAR:
                #This is the bottom row of hue hexes
                if MouseX < WIDTH/2 + SEPARATEBAR:
                    #main gradient
                    CopyToClipboard(GraHexCode[2:])
                else:
                    #gradient complement
                    CopyToClipboard(DetermineComplementHex(GraHexCode)[1:])
                    
            elif MouseY >= HUEBARHEIGHT + GRABARHEIGHT + 2 * HUEHEXBOXHEIGHT + 4 * SEPARATEBAR and MouseY < HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + 2 * HUEHEXBOXHEIGHT + 4 * SEPARATEBAR:
                #This is the Grey scale region
                GscHexCode = GreyScaleList[round(MouseX / GreyScaleScaler)]
                MutedGradientList = ConvertToHex(CreateMutedGradient(TempGreyedHex[0]))
             
            elif MouseY >= HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + 2 * HUEHEXBOXHEIGHT + 5 * SEPARATEBAR and MouseY < HUEBARHEIGHT + GRABARHEIGHT + GSCBARHEIGHT + MTDBARHEIGHT + 2 * HUEHEXBOXHEIGHT + 5 * SEPARATEBAR:
                #This is the muted gradient region
                MtdHexCode = MutedGradientList[round(MouseX / MutedScaleScaler)]
                
            else:
                #This is the catch-all for the bottom row hexes.
                if MouseX < WIDTH/4:
                    #muted main
                    CopyToClipboard(MtdHexCode[2:])
                elif MouseX < WIDTH/2:
                    #complement
                    CopyToClipboard(DetermineComplementHex(MtdHexCode)[1:])
                elif MouseX < WIDTH/(4/3):
                    #triad 1
                    CopyToClipboard(DetermineTriadicHexes(MtdHexCode)[0][1:])
                elif MouseX < WIDTH/1:
                    #triad 2
                    CopyToClipboard(DetermineTriadicHexes(MtdHexCode)[1][1:])
                

                

            
                
    elif pygame.mouse.get_pressed()[2] == True:
        print(TempGreyedHex[0])

        

                


            
pygame.quit()

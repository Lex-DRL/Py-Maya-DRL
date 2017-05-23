'''
require:
    python
    OpenImageIO
    OpenColorIO
    ffmpeg 64-bit Static            http://ffmpeg.zeranoe.com/builds/
'''

#region initialisation

import sys, os, re, glob, subprocess, time, shutil, socket, json
import OpenImageIO.OpenImageIO as oiio
# from ctypes import windll, create_unicode_buffer
from multiprocessing import Pool

ffmpeg = r"\\store\library\SequenceToMovie\ffmpeg.exe"
logo = r"\\store\library\SequenceToMovie\logo_256.png"   #should exist with alpha channel
ArtistList = r'\\STORE\library\SequenceToMovie\ArtistList.txt'
TMP = os.environ['TMP']
os.putenv("OCIO", r"\\store\library\sequenceToMovie\config.ocio")

slate = True
info = True
cache = 2.35
cache = False
fps = 25
res = (1280, 720)

settings = dict(slate = False,
                info = False,
                cache = False,
                fps = 25,
                res = (1280, 720),
                codec = "mjpeg")

# json.dump(settings, open(r'\\STORE\library\SequenceToMovie\settings.json', 'w'), indent=4)

spaces = {'exr': 'linear',
          'tif': 'linear',

          'dpx': 'cineon',

          'jpg': 'srgb',
          'png': 'srgb',
          'tga': 'srgb', }

input_file = ""
try:
    input_file = sys.argv[1]
except:
    pass

#endregion

# #hack for 8.3 format
# buf = create_unicode_buffer(500)
# windll.kernel32.GetLongPathNameW(unicode(input_file), buf, 500)
# input_file = buf.value

def getSettings(fullpath):
    split = fullpath.replace('\\','/').split('/')
    while split:
        split.pop(-1)
        path = '/'.join(split + ['settings.json'])
        if os.path.exists(path):
            settings = json.load(open(path))
            return settings
    return False


def getArtistName():
    try:
        return sys.argv[2]
    except:
        name = socket.gethostname()
        if ArtistList:
            with open(ArtistList, 'r') as f:
                lines = f.readlines()
            d = {}
            for i in range(0, len(lines)):
                sl = lines[i].strip().split('=')
                d[sl[0]] = sl[1]
            try:
                name = d[name]
            except:
                pass
        return name

def convert(arg):
    file, index, tmp, numFrames, res, space, info, cache, logo, project, episode, shot, version = arg

    frameNumber = re.findall(r'\d+', file)[-1]
    img = oiio.ImageBuf(str(file))
    spec = img.spec()


    if spec.nchannels != 3:
        dest = oiio.ImageBuf()
        oiio.ImageBufAlgo.channels(dest, img, ('R', 'G', 'B'))
        img = dest

    if res != (spec.width, spec.height):
        out = oiio.ImageBuf(oiio.ImageSpec(res[0], res[1], 3, oiio.FLOAT))
        oiio.ImageBufAlgo.resample(out, img)
        img = out

    if space != 'srgb':
        oiio.ImageBufAlgo.colorconvert(img, img, space, 'srgb')

    if cache:
        clr = (0.05, 0.05, 0.05)
        stripe = int(0.5 * (res[1] - (res[0] / cache)))
        oiio.ImageBufAlgo.fill(img, clr, oiio.ROI(0, res[0], 0, stripe))
        oiio.ImageBufAlgo.fill(img, clr, oiio.ROI(0, res[0], res[1] - stripe, res[1]))

    if info:
        clr = (0.75, 0.75, 0.75)
        oiio.ImageBufAlgo.render_text(img, 20, 700, str(project), 18, "Arial", clr)
        oiio.ImageBufAlgo.render_text(img, 220, 700, 'episode '+ str(episode)+' shot ' +str(shot), 18, "Arial", clr)
        oiio.ImageBufAlgo.render_text(img, 430, 700, 'ver ' + str(version), 18, "Arial", clr)
        oiio.ImageBufAlgo.render_text(img, 1050, 700, str(index + 1) + '(' + str(numFrames) + ')', 18, "Arial", clr)
        oiio.ImageBufAlgo.render_text(img, 1150, 700, str(frameNumber), 18, "Arial", clr)

    if logo:
        size = 100
        buf = oiio.ImageBuf(oiio.ImageSpec(res[0], res[1], 4, oiio.FLOAT))
        out = oiio.ImageBuf(oiio.ImageSpec(res[0], res[1], 4, oiio.FLOAT))
        back = oiio.ImageBuf()
        oiio.ImageBufAlgo.channels(back, img, ('R', 'G', 'B', 1.0))
        logo = oiio.ImageBuf(logo)
        logoResized = oiio.ImageBuf(oiio.ImageSpec(size, size, 4, oiio.FLOAT))
        oiio.ImageBufAlgo.resample(logoResized, logo)
        if cache:
            oiio.ImageBufAlgo.paste(buf, (res[0] - size) / 2, 0, 0, 0, logoResized)
        else:
            oiio.ImageBufAlgo.paste(buf, (res[0] - size - 5), 0, 0, 0, logoResized)
        oiio.ImageBufAlgo.over(out, buf, back)
        img = out

    outfile = tmp + "temp." + str(index + 1).zfill(4) + ".jpg"
    img.write(outfile)


if __name__ == '__main__':
    if os.path.exists(input_file):
        newsettings = getSettings(input_file)
        if newsettings:
            settings = newsettings
        temporaryDirectory = TMP + "\\seq2movie" + str(time.time()) + "\\"
        if not os.path.exists(temporaryDirectory):
            os.makedirs(temporaryDirectory)

        directory = os.path.dirname(input_file)
        fileName = os.path.basename(input_file)
        segNum = re.findall(r'\d+', input_file)[-1]
        numPad = len(segNum)
        baseName = fileName.split(segNum)[0]
        if baseName[-1] in [".", "_", "#"]:
            outName = baseName[:-1]
        fileType = fileName.split('.')[-1]
        space = spaces[fileType]

        globString = directory + '/' + baseName + '?' * numPad + '.' + fileType
        theGlob = glob.glob(globString)
        theGlob.sort()

        numFrames = len(theGlob)

        firstFrame = theGlob[0]
        firstFrameNum = re.findall(r'\d+', firstFrame)[-1]

        lastFrame = theGlob[-1]
        lastFrameNum = re.findall(r'\d+', lastFrame)[-1]

        all_tasks = []
        t = time.time()
        date = time.strftime("%d %b %Y", time.gmtime())

        try:
            project = re.findall(r'(?:PROJECTS\\)+(?P<project>[^\\]+)', input_file, re.I)[-1]
        except:
            project = 'unknown'

        shot = 'unknown'
        try:
            shot = re.findall('sh_(?P<shot>\d+)', input_file)[0]
        except:
            pass
        
        try:
            shot = re.findall('sh(?P<shot>\d+)', input_file)[0]
        except:
            pass

        #try:
        #    shot = re.findall(r'\\(?P<shot>(?:\w+_)?\w+_\d+)\\', input_file)[0]
        #except:
        #    pass
            
        episode = 'unknown'
        try:
            episode = re.findall('ep_(?P<episode>\d+)', input_file)[0]
        except:
            pass
        
        try:
            episode = re.findall('part(?P<episode>\d+)', input_file)[0]
        except:
            pass

        try:
            version = re.findall('v(?P<version>\d+)', input_file)[0]
        except:
            version = 'unknown'

        args = zip(theGlob, xrange(numFrames),
                   [temporaryDirectory] * numFrames,
                   [numFrames] * numFrames,
                   [settings['res']] * numFrames,
                   [space] * numFrames,
                   [settings['info']] * numFrames,
                   [settings['cache']] * numFrames,
                   [logo] * numFrames,
                   [project] * numFrames,
                   [episode] * numFrames,
                   [shot] * numFrames,
                   [version] * numFrames,
        )

        pool = Pool()
        #pool = Pool(processes=4)
        result = pool.imap_unordered(convert, args)
        pool.close()
        while result._index != numFrames:
            sys.stdout.write('conversion '+str(int(100 * (float(result._index) / float(numFrames))))+'%\n')
            sys.stdout.flush()
            #print int(100 * (float(result._index) / float(numFrames))), '%'
            time.sleep(1)

        if settings['slate']:
            img = oiio.ImageBuf(oiio.ImageSpec(res[0], res[1], 3, oiio.FLOAT))
            #oiio.ImageBufAlgo.fill(img,(0.05,0.05,0.05))
            oiio.ImageBufAlgo.paste(img, (res[0] - 256) / 2, 0, 0, 0, oiio.ImageBuf(str(logo)))
            n = 0
            for i in (theGlob[0], theGlob[numFrames / 2], theGlob[-1]):
                thumb = oiio.ImageBuf(str(i))
                if thumb.spec().nchannels != 3:
                    dest = oiio.ImageBuf()
                    oiio.ImageBufAlgo.channels(dest, thumb, ('R', 'G', 'B'))
                    thumb = dest
                if space != 'srgb':
                    oiio.ImageBufAlgo.colorconvert(thumb, thumb, space, 'srgb')
                thumb_mini = oiio.ImageBuf(oiio.ImageSpec(400, 225, 3, oiio.FLOAT))
                oiio.ImageBufAlgo.resample(thumb_mini, thumb)
                oiio.ImageBufAlgo.paste(img, (20, 440, 860)[n], 250, 0, 0, thumb_mini)
                n += 1

            clr = (0.75, 0.75, 0.75)

            oiio.ImageBufAlgo.render_text(img, 50, 600, 'project ' + str(project), 18, "Arial", clr)
            oiio.ImageBufAlgo.render_text(img, 50, 630, 'episode '+str(episode)+' shot '+str(shot), 18, "Arial", clr)
            oiio.ImageBufAlgo.render_text(img, 50, 660, 'version ' + str(version), 18, "Arial", clr)
            oiio.ImageBufAlgo.render_text(img, 50, 690, str(date), 18, "Arial", clr)
            oiio.ImageBufAlgo.render_text(img, 800, 660, str(settings["fps"]) + ' fps', 18, "Arial", clr)
            oiio.ImageBufAlgo.render_text(img, 800, 630, getArtistName(), 18, "Arial", clr)
            oiio.ImageBufAlgo.render_text(img, 800, 690, str(int(lastFrameNum) - int(firstFrameNum) + 1) + ' frames',
                                          18, "Arial", clr)
            oiio.ImageBufAlgo.render_text(img, 1000, 690, str(firstFrameNum) + ' - ' + str(lastFrameNum), 18, "Arial",
                                          clr)

            tempFrame = temporaryDirectory + "temp.0000.jpg"
            img.write(tempFrame)
        sys.stdout.write("conversion 100%\n")
        #print "100 %"
        #sys.stdout.write("time:"+str(time.time() - t)+"\n")
        print "time:", time.time() - t
        dailisDir = ""

        inFile = temporaryDirectory + 'temp.%4d.jpg'
        #outFile = directory + "\\" + outName + ".mp4"
        #outFile = directory + "\\" + outName + ".mov"
        directory = '/'.join(directory.replace('\\','/').split('/')[:-1])
        outFile = directory+"/ep_"+str(episode)+"_sh_"+str(shot)+"_v"+str(version)+".mov"
        command = [ffmpeg, "-f", "image2",
                   "-i", inFile,
                   "-r", str(settings["fps"]),
                   "-vcodec", settings["codec"],
                   "-q:v", "1",
                   outFile, "-y"]
        # -start_number
        s = subprocess.Popen(command)
        s.wait()
        shutil.rmtree(temporaryDirectory)
        
        if len(sys.argv) == 2:
            dailisDir = False
            try:
                dailisDir = re.findall(r'(.*(?:PROJECTS\\)+(?:[^\\]+))', input_file, re.I)[0]
                dailisDir+='\\out\\dailies\\'+ time.strftime("%Y%m%d", time.gmtime())
            except:
                pass
            if dailisDir:
                if not os.path.exists(dailisDir):
                    os.makedirs(dailisDir)
                folder = 'explorer "'+os.path.abspath(directory)+'"'
                subprocess.Popen(folder)
                subprocess.Popen('explorer "'+dailisDir+'"')

    else:
        print "Drop any frame of sequence on SequenceToMovie shortcut"
        raw_input()
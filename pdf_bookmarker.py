import re
import sys

from distutils.version import LooseVersion
from os.path import exists, splitext
from PyPDF2 import PdfFileReader, PdfFileWriter

from pdfrw import PdfReader, PdfWriter, PageMerge, IndirectPdfDict, PdfArray, PdfName, PdfObject, PdfString
from pdfrw.errors import PdfOutputError
from datetime import datetime

is_python2 = LooseVersion(sys.version) < '3'

class NewPdfWriter(PdfWriter):

    def __init__(self, version='1.3', compress=False):
        self._bookmarks = []
        self._bookmarksDict = {}
        self._info = None

        super(NewPdfWriter, self).__init__(version, compress)
        
    def addBookmark(self, title, pageNum, parent = None):
        '''
        Adds a new bookmark entry.
        pageNum must be a valid page number in the writer
        and parent can be a bookmark object returned by a previous addBookmark call
        '''
                
        try:
            page = self.pagearray[pageNum]
        except IndexError:
            # TODO: Improve error handling ?
            PdfOutputError("Invalid page number: " % (pageNum))
            
        bookmark = {
            'title': title,
            'page': page,
            'childs': []
        }
        bid = id(bookmark)        
        
        if not parent:            
            self._bookmarks.append(bookmark)        
            
        else:
            parentObj = self._bookmarksDict.get(id(parent), None)
            if not parentObj:
                PdfOutputError("Bookmark parent object not found: " % parent)
                        
            parentObj['childs'].append(bookmark)
                        
        self._bookmarksDict[bid] = bookmark
        return bookmark
        
    def setInfo(self, info):
        '''
        Sets pdf metadata, info must be a dict where each key is the metadata key
        standard/known keys are:
            Title
            Author
            Creator
            Producer
        '''
        self._info = info
        
    def write(self, fname, trailer=None, user_fmt=None, disable_gc=True):        
            
        # Recursive function to build outlines tree
        def buildOutlines(parent, bookmarks):
            
            outline = None
            
            if bookmarks:
                outline = IndirectPdfDict()
                outline.Count = len(bookmarks)
                
                first = None
                next = None
                last = None
                                       
                for b in bookmarks:
                    
                    newb = IndirectPdfDict(
                        Parent = parent or outline,
                        Title = b['title'],
                        A = IndirectPdfDict(
                            D = PdfArray( (b['page'], PdfName('Fit')) ),
                            S = PdfName('GoTo')
                        )
                    ) 
                    
                    if not first:
                        first = newb
                        
                    else:
                        last.Next = newb
                        newb.Prev = last                                              
                        
                    last = newb
                    
                    # Add children, if any.
                    if b['childs']:
                        childOutline = buildOutlines(newb, b['childs'])
                        newb.First = childOutline.First
                        newb.Last = childOutline.Last
                        newb.Count = childOutline.Count
                        
                        
                outline.First = first
                outline.Last = last
                     
            return outline
            
        # Testing for now, only add root level bookmarks
        outlines = buildOutlines(None, self._bookmarks)
                       
        # If not custom trailer is given and we have info to set.
        # set info on self trailer
        if not trailer:
            if self._info:
                self.trailer.Info = IndirectPdfDict(**self._info)            
                
            if outlines:
                self.trailer.Root.Outlines = outlines
        
        
        # if user_fmt is given use it otherwise use default from pdfrw
        # this if is not necessary if this code is moved into the actual writer, did it this way
        # for now to avoid adding a reference to user_fmt
        if user_fmt:
            super(NewPdfWriter, self).write(fname, trailer, user_fmt, disable_gc)
        else:
            super(NewPdfWriter, self).write(fname, trailer, disable_gc=disable_gc)
            
def _get_parent_bookmark(current_indent, history_indent, bookmarks):
    '''The parent of A is the nearest bookmark whose indent is smaller than A's
    '''
    assert len(history_indent) == len(bookmarks)
    if current_indent == 0:
        return None
    for i in range(len(history_indent) - 1, -1, -1):
        # len(history_indent) - 1   ===>   0
        if history_indent[i] < current_indent:
            return bookmarks[i]
    return None

def addBookmark(pdf_path, bookmark_txt_path, page_offset):
    if not exists(pdf_path):
        return "Error: No such file: {}".format(pdf_path)
    if not exists(bookmark_txt_path):
        return "Error: No such file: {}".format(bookmark_txt_path)

    with open(bookmark_txt_path, 'r', encoding='utf-8') as f:
        bookmark_lines = f.readlines()
    reader = PdfFileReader(pdf_path)
    writer = PdfFileWriter()
    writer.cloneDocumentFromReader(reader)

    maxPages = reader.getNumPages()
    bookmarks, history_indent = [], []
    # decide the level of each bookmark according to the relative indent size in each line
    #   no indent:          level 1
    #     small indent:     level 2
    #       larger indent:  level 3
    #   ...
    for line in bookmark_lines:
        line2 = re.split(r'\s+', unicode(line.strip(), 'utf-8')) if is_python2 else re.split(r'\s+', line.strip())
        if len(line2) == 1:
            continue

        indent_size = len(line) - len(line.lstrip())
        parent = _get_parent_bookmark(indent_size, history_indent, bookmarks)
        history_indent.append(indent_size)

        title, page = ' '.join(line2[:-1]), int(line2[-1]) - 1
        if page + page_offset >= maxPages:
            return "Error: page index out of range: %d >= %d" % (page + page_offset, maxPages)
        new_bookmark = writer.addBookmark(title, page + page_offset, parent=parent)
        bookmarks.append(new_bookmark)

    out_path = splitext(pdf_path)[0] + '_bookmark_added.pdf'
    with open(out_path,'wb') as f:
        writer.write(f)

    return "The bookmarks have been added to %s" % out_path

def processIndent(bookmark_txt_path):
    if not exists(bookmark_txt_path):
        return "Error: No such file: {}".format(bookmark_txt_path)

    with open(bookmark_txt_path, 'r', encoding='utf-8') as f:
        bookmark_lines = f.readlines()

    result_lines = []
    secondary_directory = re.compile(r'\d+.\d+', re.DOTALL)
    third_directory = re.compile(r'\d+.\d+.\d+', re.DOTALL)
    for line in bookmark_lines:
        line2 = re.split(r'\s+', unicode(line.strip(), 'utf-8')) if is_python2 else re.split(r'\s+', line.strip())

        line3 = line.lstrip()
        if re.match(secondary_directory, line2[0]) != None:
            if re.match(third_directory, line2[0]) != None:
                result_lines.append('    ' + line3)
            else:
                result_lines.append('  ' + line3)
        else:
            result_lines.append(line3)

    out_path = splitext(bookmark_txt_path)[0] + '_indents_added.txt'
    with open(out_path,'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    return "The indents have been added to %s" % out_path

def removeBookmark(pdf_path):
    totalPages = 0
    output = NewPdfWriter()

    reader = None
    f = open(pdf_path, 'rb')
    
    try:
        reader = PdfReader(f)
        
        pdfPages = 0

        for page in reader.pages:
            output.addpage(page)
            pdfPages += 1                                 

        bmname = 'Bm (%s) - %s' % (1, 'Root')
            
        totalPages += pdfPages
        
    finally:     
        f.close()
        if reader: del reader

    pdf_name = splitext(pdf_path)[0]

    output.setInfo({
        'Title': pdf_name,
        'Author':'first dude',
        'Creator':'second dude',
        'Producer':'third dude',
        'Created': datetime.now().isoformat()
    })

    out_path = pdf_name + '_bookmark_removed.pdf'
    output.write(open(out_path, 'wb'))

    return "The bookmarks have been removed in %s" % out_path

if __name__ == "__main__":
    import sys
    args = sys.argv
    if len(args) == 2:
        print(processIndent(args[1]))
    elif len(args) == 3:
        print(removeBookmark(args[2]))
    elif len(args) == 4:
        print(addBookmark(args[1], args[2], int(args[3])))
    else:
       print("Usage:\n")
       print("Add Bookmarks\n\tpdf_bookmarker.py [pdf] [bookmark_txt] [page_offset]")
       print("Remove Bookmarks\n\t pdf_bookmarker.py -r [pdf]")
       print("Add Indents\n\t pdf_bookmarker.py [bookmark_txt]")
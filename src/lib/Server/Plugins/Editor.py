import Bcfg2.Server.Plugin
import fileinput
import re
import lxml.etree
from getopt import getopt

def linesub(pattern, repl, filestring):
    if filestring == None:
        filestring = ''
    output = list()
    fileread = filestring.split('\n')
    for line in fileread:
        output.append(re.sub(pattern, repl, filestring))
    return '\n'.join(output)

class EditDirectives(Bcfg2.Server.Plugin.SpecificData):
    def ProcessDirectives(self, input):
        temp = input
        for directive in self.data.split('\n'):
            directive = directive.split(',')
            temp = linesub(directive[0], directive[1], temp)
        return temp

class EditEntrySet(Bcfg2.Server.Plugin.EntrySet):
    def __init__(self, basename, path, props, entry_type, encoding):
        Bcfg2.Server.Plugin.EntrySet.__init__(self, basename, path, props, entry_type, encoding)
        self.inputs = dict()

    def bind_entry(self, entry, metadata):
        client = metadata.hostname
        filename = entry.get('name')
        permdata = {'owner':'root', 'group':'root'}
        permdata['perms'] = '0644'
        [entry.attrib.__setitem__(key, permdata[key]) for key in permdata]
        entry.text = self.entries['edits'].ProcessDirectives(self.get_client_data(client))
        if not entry.text:
            entry.set('empty', 'true')

    def get_client_data(self, client):
        return self.inputs[client]


class Editor(Bcfg2.Server.Plugin.GroupSpool,Bcfg2.Server.Plugin.ProbingPlugin):
    __name__ = 'Editor'
    __version__ = '1'
    __author__ = 'bcfg2-dev@mcs.anl.gov'
    filename_pattern = 'edits'
    es_child_cls = EditDirectives
    es_cls = EditEntrySet

    def GetProbes(self, _):
        probelist = list()
        for name in self.entries.keys():
            probe = lxml.etree.Element('probe')
            probe.set('name', name)
            probe.set('source', "Editor")
            probe.text = "cat %s" %name
            probelist.append(probe)
        return probelist

    def ReceiveData(self, client, datalist):
        for data in datalist:
            self.entries[data.get('name')].inputs[client.hostname] = data.text
            print data, data.attrib

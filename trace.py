##########################################################################
#
# Copyright 2008-2010 VMware, Inc.
# All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
##########################################################################/

"""Common trace code generation."""


import specs.stdapi as stdapi


def interface_wrap_name(interface):
    return "Wrap" + interface.expr


class ComplexValueSerializer(stdapi.OnceVisitor):
    '''Type visitors which generates serialization functions for
    complex types.
    
    Simple types are serialized inline.
    '''

    def __init__(self, serializer):
        stdapi.OnceVisitor.__init__(self)
        self.serializer = serializer

    def visitVoid(self, literal):
        pass

    def visitLiteral(self, literal):
        pass

    def visitString(self, string):
        pass

    def visitConst(self, const):
        self.visit(const.type)

    def visitStruct(self, struct):
        for type, name in struct.members:
            self.visit(type)
        print 'static void _write__%s(const %s &value) {' % (struct.tag, struct.expr)
        print '    static const char * members[%u] = {' % (len(struct.members),)
        for type, name,  in struct.members:
            print '        "%s",' % (name,)
        print '    };'
        print '    static const trace::StructSig sig = {'
        print '       %u, "%s", %u, members' % (struct.id, struct.name, len(struct.members))
        print '    };'
        print '    trace::localWriter.beginStruct(&sig);'
        for type, name in struct.members:
            self.serializer.visit(type, 'value.%s' % (name,))
        print '    trace::localWriter.endStruct();'
        print '}'
        print

    def visitArray(self, array):
        self.visit(array.type)

    def visitBlob(self, array):
        pass

    def visitEnum(self, enum):
        print 'static const trace::EnumValue __enum%s_values[] = {' % (enum.tag)
        for value in enum.values:
            print '   {"%s", %s},' % (value, value)
        print '};'
        print
        print 'static const trace::EnumSig __enum%s_sig = {' % (enum.tag)
        print '   %u, %u, __enum%s_values' % (enum.id, len(enum.values), enum.tag)
        print '};'
        print

    def visitBitmask(self, bitmask):
        print 'static const trace::BitmaskFlag __bitmask%s_flags[] = {' % (bitmask.tag)
        for value in bitmask.values:
            print '   {"%s", %s},' % (value, value)
        print '};'
        print
        print 'static const trace::BitmaskSig __bitmask%s_sig = {' % (bitmask.tag)
        print '   %u, %u, __bitmask%s_flags' % (bitmask.id, len(bitmask.values), bitmask.tag)
        print '};'
        print

    def visitPointer(self, pointer):
        self.visit(pointer.type)

    def visitHandle(self, handle):
        self.visit(handle.type)

    def visitAlias(self, alias):
        self.visit(alias.type)

    def visitOpaque(self, opaque):
        pass

    def visitInterface(self, interface):
        print "class %s : public %s " % (interface_wrap_name(interface), interface.name)
        print "{"
        print "public:"
        print "    %s(%s * pInstance);" % (interface_wrap_name(interface), interface.name)
        print "    virtual ~%s();" % interface_wrap_name(interface)
        print
        for method in interface.iterMethods():
            print "    " + method.prototype() + ";"
        print
        #print "private:"
        print "    %s * m_pInstance;" % (interface.name,)
        print "};"
        print

    def visitPolymorphic(self, polymorphic):
        print 'static void _write__%s(int selector, const %s & value) {' % (polymorphic.tag, polymorphic.expr)
        print '    switch (selector) {'
        for cases, type in polymorphic.iterSwitch():
            for case in cases:
                print '    %s:' % case
            self.serializer.visit(type, 'static_cast<%s>(value)' % (type,))
            print '        break;'
        print '    }'
        print '}'
        print


class ValueSerializer(stdapi.Visitor):
    '''Visitor which generates code to serialize any type.
    
    Simple types are serialized inline here, whereas the serialization of
    complex types is dispatched to the serialization functions generated by
    ComplexValueSerializer visitor above.
    '''

    def visitLiteral(self, literal, instance):
        print '    trace::localWriter.write%s(%s);' % (literal.kind, instance)

    def visitString(self, string, instance):
        if string.length is not None:
            print '    trace::localWriter.writeString((const char *)%s, %s);' % (instance, string.length)
        else:
            print '    trace::localWriter.writeString((const char *)%s);' % instance

    def visitConst(self, const, instance):
        self.visit(const.type, instance)

    def visitStruct(self, struct, instance):
        print '    _write__%s(%s);' % (struct.tag, instance)

    def visitArray(self, array, instance):
        length = '__c' + array.type.tag
        index = '__i' + array.type.tag
        print '    if (%s) {' % instance
        print '        size_t %s = %s;' % (length, array.length)
        print '        trace::localWriter.beginArray(%s);' % length
        print '        for (size_t %s = 0; %s < %s; ++%s) {' % (index, index, length, index)
        print '            trace::localWriter.beginElement();'
        self.visit(array.type, '(%s)[%s]' % (instance, index))
        print '            trace::localWriter.endElement();'
        print '        }'
        print '        trace::localWriter.endArray();'
        print '    } else {'
        print '        trace::localWriter.writeNull();'
        print '    }'

    def visitBlob(self, blob, instance):
        print '    trace::localWriter.writeBlob(%s, %s);' % (instance, blob.size)

    def visitEnum(self, enum, instance):
        print '    trace::localWriter.writeEnum(&__enum%s_sig, %s);' % (enum.tag, instance)

    def visitBitmask(self, bitmask, instance):
        print '    trace::localWriter.writeBitmask(&__bitmask%s_sig, %s);' % (bitmask.tag, instance)

    def visitPointer(self, pointer, instance):
        print '    if (%s) {' % instance
        print '        trace::localWriter.beginArray(1);'
        print '        trace::localWriter.beginElement();'
        self.visit(pointer.type, "*" + instance)
        print '        trace::localWriter.endElement();'
        print '        trace::localWriter.endArray();'
        print '    } else {'
        print '        trace::localWriter.writeNull();'
        print '    }'

    def visitHandle(self, handle, instance):
        self.visit(handle.type, instance)

    def visitAlias(self, alias, instance):
        self.visit(alias.type, instance)

    def visitOpaque(self, opaque, instance):
        print '    trace::localWriter.writeOpaque((const void *)%s);' % instance

    def visitInterface(self, interface, instance):
        print '    trace::localWriter.writeOpaque((const void *)&%s);' % instance

    def visitPolymorphic(self, polymorphic, instance):
        print '    _write__%s(%s, %s);' % (polymorphic.tag, polymorphic.switchExpr, instance)


class ValueWrapper(stdapi.Visitor):
    '''Type visitor which will generate the code to wrap an instance.
    
    Wrapping is necessary mostly for interfaces, however interface pointers can
    appear anywhere inside complex types.
    '''

    def visitVoid(self, type, instance):
        raise NotImplementedError

    def visitLiteral(self, type, instance):
        pass

    def visitString(self, type, instance):
        pass

    def visitConst(self, type, instance):
        pass

    def visitStruct(self, struct, instance):
        for type, name in struct.members:
            self.visit(type, "(%s).%s" % (instance, name))

    def visitArray(self, array, instance):
        # XXX: actually it is possible to return an array of pointers
        pass

    def visitBlob(self, blob, instance):
        pass

    def visitEnum(self, enum, instance):
        pass

    def visitBitmask(self, bitmask, instance):
        pass

    def visitPointer(self, pointer, instance):
        print "    if (%s) {" % instance
        self.visit(pointer.type, "*" + instance)
        print "    }"

    def visitHandle(self, handle, instance):
        self.visit(handle.type, instance)

    def visitAlias(self, alias, instance):
        self.visit(alias.type, instance)

    def visitOpaque(self, opaque, instance):
        pass
    
    def visitInterface(self, interface, instance):
        assert instance.startswith('*')
        instance = instance[1:]
        print "    if (%s) {" % instance
        print "        %s = new %s(%s);" % (instance, interface_wrap_name(interface), instance)
        print "    }"
    
    def visitPolymorphic(self, type, instance):
        # XXX: There might be polymorphic values that need wrapping in the future
        pass


class ValueUnwrapper(ValueWrapper):
    '''Reverse of ValueWrapper.'''

    def visitInterface(self, interface, instance):
        assert instance.startswith('*')
        instance = instance[1:]
        print "    if (%s) {" % instance
        print "        %s = static_cast<%s *>(%s)->m_pInstance;" % (instance, interface_wrap_name(interface), instance)
        print "    }"


class Tracer:
    '''Base class to orchestrate the code generation of API tracing.'''

    def __init__(self):
        self.api = None

    def serializerFactory(self):
        '''Create a serializer.
        
        Can be overriden by derived classes to inject their own serialzer.
        '''

        return ValueSerializer()

    def trace_api(self, api):
        self.api = api

        self.header(api)

        # Includes
        for header in api.headers:
            print header
        print

        # Generate the serializer functions
        types = api.all_types()
        visitor = ComplexValueSerializer(self.serializerFactory())
        map(visitor.visit, types)
        print

        # Interfaces wrapers
        interfaces = [type for type in types if isinstance(type, stdapi.Interface)]
        map(self.traceInterfaceImpl, interfaces)
        print

        # Function wrappers
        map(self.traceFunctionDecl, api.functions)
        map(self.traceFunctionImpl, api.functions)
        print

        self.footer(api)

    def header(self, api):
        pass

    def footer(self, api):
        pass

    def traceFunctionDecl(self, function):
        # Per-function declarations

        if function.args:
            print 'static const char * __%s_args[%u] = {%s};' % (function.name, len(function.args), ', '.join(['"%s"' % arg.name for arg in function.args]))
        else:
            print 'static const char ** __%s_args = NULL;' % (function.name,)
        print 'static const trace::FunctionSig __%s_sig = {%u, "%s", %u, __%s_args};' % (function.name, function.id, function.name, len(function.args), function.name)
        print

    def isFunctionPublic(self, function):
        return True

    def traceFunctionImpl(self, function):
        if self.isFunctionPublic(function):
            print 'extern "C" PUBLIC'
        else:
            print 'extern "C" PRIVATE'
        print function.prototype() + ' {'
        if function.type is not stdapi.Void:
            print '    %s __result;' % function.type
        self.traceFunctionImplBody(function)
        if function.type is not stdapi.Void:
            self.wrapRet(function, "__result")
            print '    return __result;'
        print '}'
        print

    def traceFunctionImplBody(self, function):
        print '    unsigned __call = trace::localWriter.beginEnter(&__%s_sig);' % (function.name,)
        for arg in function.args:
            if not arg.output:
                self.unwrapArg(function, arg)
                self.serializeArg(function, arg)
        print '    trace::localWriter.endEnter();'
        self.invokeFunction(function)
        print '    trace::localWriter.beginLeave(__call);'
        for arg in function.args:
            if arg.output:
                self.serializeArg(function, arg)
                self.wrapArg(function, arg)
        if function.type is not stdapi.Void:
            self.serializeRet(function, "__result")
        print '    trace::localWriter.endLeave();'

    def invokeFunction(self, function, prefix='__', suffix=''):
        if function.type is stdapi.Void:
            result = ''
        else:
            result = '__result = '
        dispatch = prefix + function.name + suffix
        print '    %s%s(%s);' % (result, dispatch, ', '.join([str(arg.name) for arg in function.args]))

    def serializeArg(self, function, arg):
        print '    trace::localWriter.beginArg(%u);' % (arg.index,)
        self.serializeArgValue(function, arg)
        print '    trace::localWriter.endArg();'

    def serializeArgValue(self, function, arg):
        self.serializeValue(arg.type, arg.name)

    def wrapArg(self, function, arg):
        self.wrapValue(arg.type, arg.name)

    def unwrapArg(self, function, arg):
        self.unwrapValue(arg.type, arg.name)

    def serializeRet(self, function, instance):
        print '    trace::localWriter.beginReturn();'
        self.serializeValue(function.type, instance)
        print '    trace::localWriter.endReturn();'

    def serializeValue(self, type, instance):
        serializer = self.serializerFactory()
        serializer.visit(type, instance)

    def wrapRet(self, function, instance):
        self.wrapValue(function.type, instance)

    def unwrapRet(self, function, instance):
        self.unwrapValue(function.type, instance)

    def wrapValue(self, type, instance):
        visitor = ValueWrapper()
        visitor.visit(type, instance)

    def unwrapValue(self, type, instance):
        visitor = ValueUnwrapper()
        visitor.visit(type, instance)

    def traceInterfaceImpl(self, interface):
        print '%s::%s(%s * pInstance) {' % (interface_wrap_name(interface), interface_wrap_name(interface), interface.name)
        print '    m_pInstance = pInstance;'
        print '}'
        print
        print '%s::~%s() {' % (interface_wrap_name(interface), interface_wrap_name(interface))
        print '}'
        print
        for method in interface.iterMethods():
            self.traceMethod(interface, method)
        print

    def traceMethod(self, interface, method):
        print method.prototype(interface_wrap_name(interface) + '::' + method.name) + ' {'
        print '    static const char * __args[%u] = {%s};' % (len(method.args) + 1, ', '.join(['"this"'] + ['"%s"' % arg.name for arg in method.args]))
        print '    static const trace::FunctionSig __sig = {%u, "%s", %u, __args};' % (method.id, interface.name + '::' + method.name, len(method.args) + 1)
        print '    unsigned __call = trace::localWriter.beginEnter(&__sig);'
        print '    trace::localWriter.beginArg(0);'
        print '    trace::localWriter.writeOpaque((const void *)m_pInstance);'
        print '    trace::localWriter.endArg();'
        for arg in method.args:
            if not arg.output:
                self.unwrapArg(method, arg)
                self.serializeArg(method, arg)
        if method.type is stdapi.Void:
            result = ''
        else:
            print '    %s __result;' % method.type
            result = '__result = '
        print '    trace::localWriter.endEnter();'
        print '    %sm_pInstance->%s(%s);' % (result, method.name, ', '.join([str(arg.name) for arg in method.args]))
        print '    trace::localWriter.beginLeave(__call);'
        for arg in method.args:
            if arg.output:
                self.serializeArg(method, arg)
                self.wrapArg(method, arg)
        if method.type is not stdapi.Void:
            print '    trace::localWriter.beginReturn();'
            self.serializeValue(method.type, "__result")
            print '    trace::localWriter.endReturn();'
            self.wrapValue(method.type, '__result')
        print '    trace::localWriter.endLeave();'
        if method.name == 'QueryInterface':
            print '    if (ppvObj && *ppvObj) {'
            print '        if (*ppvObj == m_pInstance) {'
            print '            *ppvObj = this;'
            print '        }'
            for iface in self.api.interfaces:
                print r'        else if (riid == IID_%s) {' % iface.name
                print r'            *ppvObj = new Wrap%s((%s *) *ppvObj);' % (iface.name, iface.name)
                print r'        }'
            print r'        else {'
            print r'            os::log("apitrace: warning: unknown REFIID {0x%08lX,0x%04X,0x%04X,{0x%02X,0x%02X,0x%02X,0x%02X,0x%02X,0x%02X,0x%02X,0x%02X}}\n",'
            print r'                    riid.Data1, riid.Data2, riid.Data3,'
            print r'                    riid.Data4[0],'
            print r'                    riid.Data4[1],'
            print r'                    riid.Data4[2],'
            print r'                    riid.Data4[3],'
            print r'                    riid.Data4[4],'
            print r'                    riid.Data4[5],'
            print r'                    riid.Data4[6],'
            print r'                    riid.Data4[7]);'
            print r'        }'
            print '    }'
        if method.name == 'Release':
            assert method.type is not stdapi.Void
            print '    if (!__result)'
            print '        delete this;'
        if method.type is not stdapi.Void:
            print '    return __result;'
        print '}'
        print


from Token import Token
from Chario import Chario
from Scanner import Scanner


class Parser:
	"""
	The Parser class uses a recursive descent strategy
	to recognize phrases in a stream of tokens. Unlike the scanner,
	which continues to generate tokens after lexical errors,
	the parser halts execution upon encountering
	the first syntax error in a source program.
	"""
	def __init__(self, chario, scanner):
		"""
		construct a Parser instance
		
		Arguments:
			chario -- the instance of Chario
			scanner -- the instance of Scanner
		"""
		self.chario = chario
		self.scanner = scanner
		# should implement handles
		#self.initHandles()
		self.token = scanner.GetNextToken()


	def parse(self):
		"""
		do parse the entire source code
		"""
		self.subprogramBody()
		# accept EOF: check if extra symbols after logical end of program exist
		#self.accept(Token.EOF)


	def ignore_newlines(self):
		"""
		ignore preceding newlines("\n")
		"""
		while self.token.code == Token.NEWLINE:
			self.token = self.scanner.GetNextToken()


	def discard_tokens(self):
			# give up parsing the line with an error by discarding all trailling tokens until a newline character
			message = "trailing tokens: " + str(self.token) + " "
			
			self.token = self.scanner.GetNextToken()
			while self.token.code != Token.NEWLINE:
				message += str(self.token) + " "
				self.token = self.scanner.GetNextToken()
			message += "were discarded"
			
			# prepare next token other than newline for next parsing attempt
			self.ignore_newlines()

			print(message)


	def accept(self, expected, error_message):
		"""
		accept the current token only with the expected code

		Arguments:
			expected {Token.{code}} -- expected token code
			error_message {str} -- error message if unacceptable
		"""
		# prepare error message first
		error_message = "expected [" + expected + "] but " + str(self.token) + " was detected"

		# these tokens always appear that the end of a line
		line_terminating_tokens = (Token.IS, Token.LOOP, Token.SEMICOLON)

		# if the last token of this line was an unexpected one,
		# do not remove that newline to preserve the next line's tokens
		# (if we do ignore it, all the tokens in the next line will be discarded!)
		if self.token.code == Token.NEWLINE and expected in line_terminating_tokens:
			self.fatalError(error_message)
		

		self.ignore_newlines()

		if self.token.code != expected:

			# raise error!
			self.fatalError(error_message)

		self.token = self.scanner.GetNextToken()
		if expected in line_terminating_tokens:
			self.ignore_newlines()



	def fatalError(self, error_message):
		"""
		send error message to the Chario instance and throw RuntimeError

		Arguments:
			error_message {str} -- error message to send to the Chario
		"""
		self.chario.PrintErrorMessage(error_message)
		self.discard_tokens()
		raise RuntimeError("Fatal error: " + error_message)	# TODO: check the error message format


	def subprogramBody(self):
		"""
		Check whole subprogram matches to EBNF grammar for TinyAda
		"""

		try:
			self.subprogramSpecification()
			self.accept(Token.IS,
						"\'" + Token.IS + "\' expected")
		except RuntimeError as e:
			print("continue parsing from declarative part of subprogram body\n")

		try:
			self.declarativePart()
		except RuntimeError as e:
			print("continue parsing from [begin] of subprogram body\n")

		try:
			self.accept(Token.BEGIN,
						"\'" + Token.BEGIN + "\' expected")
		except RuntimeError as e:
			print("continue parsing from sequence of statement of subprogram body\n")

		try:
			self.sequenceOfStatements()
		except RuntimeError as e:
			print("continue parsing from [end] of subprogram body\n")

		try:
			self.accept(Token.END,
						"\'" + Token.END + "\' expected")
			if self.token.code == Token.ID:	# TODO: force <procedure>identifier
				self.token = self.scanner.GetNextToken()
			self.accept(Token.SEMICOLON, 
						"semicolon expected")
		except RuntimeError as e:
			print("stop parsing subprogram body\n")


	def declarativePart(self):
		while self.token.code in Token.basicDeclarationHandles:
			try:
				self.basicDeclaration()
			except RuntimeError as e:
				print("continue parsing basic declaration of declarative part\n")


	def basicDeclaration(self):
		if self.token.code == Token.ID:
			self.numberOrObjectDeclaration()
		elif self.token.code == Token.TYPE:
			self.typeDeclaration()
		elif self.token.code == Token.PROC:
			self.subprogramBody()


	def numberOrObjectDeclaration(self):
		self.identifierList()
		self.accept(Token.COLON,
					"\'" + Token.COLON + "\' expected")
		if self.token.code == Token.CONSTANT:
			self.numberDeclaration()
		else:
			self.objectDeclaration()


	def objectDeclaration(self):
		self.typeDefinition()
		self.accept(Token.SEMICOLON,
					"\'" + Token.SEMICOLON + "\' expected")


	def numberDeclaration(self):
		self.accept(Token.CONSTANT,
					"\'" + "constant" + "\' expected")
		self.accept(Token.COLON_EQ,
					"\'" + Token.COLON_EQ + "\' expected")
		self.expression()	# TODO: force <static>expression
		self.accept(Token.SEMICOLON,
					"\'" + Token.SEMICOLON + "\' expected")


	def identifierList(self):
		self.accept(Token.ID,
					"identifier expected")
		while self.token.code == Token.COMMA:
			self.token = self.scanner.GetNextToken()
			self.accept(Token.ID,
						"identifier expected")


	def typeDeclaration(self):
		self.accept(Token.TYPE,
					"\'" + Token.TYPE + "\' expected")
		self.accept(Token.ID,
					"identifier expected")
		self.accept(Token.IS,
					"\'" + Token.IS + "\' expected")
		self.typeDefinition()
		self.accept(Token.SEMICOLON,
					"\'" + Token.SEMICOLON + "\' expected")


	def typeDefinition(self):
		if self.token.code == Token.PARENTHESIS_OPEN:
			self.enumerationTypeDefinition()
		elif self.token.code == Token.ARRAY:
			self.arrayTypeDefinition()
		elif self.token.code == Token.RANGE:
			self.range()
		elif self.token.code == Token.ID:	# TODO: force <type>name
			self.name()
		else:
			self.fatalError("expected either an opening parenthesis, an array,"+\
			" a range, or an identifier but " + str(self.token) + " was detected")


	def range(self):
		self.accept(Token.RANGE,
					"\'" + Token.IS + "\' expected")
		self.simpleExpression()
		self.accept(Token.DOT_DOT,
					"\'" + Token.DOT_DOT + "\' expected")
		self.simpleExpression()


	def index(self):
		if self.token.code == Token.RANGE:
			self.range()
		elif self.token.code == Token.ID:	# TODO: force <type>name
			self.name()
		else:
			self.fatalError("error in indexing")


	def enumerationTypeDefinition(self):
		self.accept(Token.PARENTHESIS_OPEN,
					"\'" + Token.PARENTHESIS_OPEN + "\' expected")
		self.identifierList()
		self.accept(Token.PARENTHESIS_CLOSE,
					"\'" + Token.PARENTHESIS_CLOSE + "\' expected")


	def arrayTypeDefinition(self):
		self.accept(Token.ARRAY,
					"\'" + Token.ARRAY + "\' expected")
		self.accept(Token.PARENTHESIS_OPEN,
					"\'" + Token.PARENTHESIS_OPEN + "\' expected")
		self.index()
		while self.token.code == Token.COMMA:
			self.token = self.scanner.GetNextToken()
			self.index()
		self.accept(Token.PARENTHESIS_CLOSE,
					"\'" + Token.PARENTHESIS_CLOSE + "\' expected")
		self.accept(Token.OF,
					"\'" + Token.OF + "\' expected")
		self.name()	# TODO: force <type>name


	def subprogramSpecification(self):
		self.accept(Token.PROC,
					"procedure expected")
		self.accept(Token.ID,
					"identifier expected")
		if self.token.code == "(":	# TODO: note
			self.formalPart()


	def formalPart(self):
		self.accept(Token.PARENTHESIS_OPEN,
					"\'" + Token.PARENTHESIS_OPEN + "\' expected")
		self.parameterSpecification()
		while self.token.code == Token.SEMICOLON:
			self.token = self.scanner.GetNextToken()
			self.parameterSpecification()
		self.accept(Token.PARENTHESIS_CLOSE,
					"\'" + Token.PARENTHESIS_CLOSE + "\' expected")


	def parameterSpecification(self):
		self.identifierList()
		self.accept(Token.COLON,
					"\'" + Token.COLON + "\' expected")
		self.mode()
		self.name()	# TODO: force <type>name


	def mode(self):
		if self.token.code == Token.IN:
			self.token = self.scanner.GetNextToken()
		if self.token.code == Token.OUT:
			self.token = self.scanner.GetNextToken()


	def sequenceOfStatements(self):
		self.statement()
		while self.token.code not in (Token.END, Token.ELSIF, Token.ELSE):	# TODO: should be implemented -> done
			self.statement()


	def statement(self):	# TODO: should be implemented
		try:
			if self.token.code in (Token.IF, Token.WHILE, Token.LOOP):
				self.compoundStatement()
			else:
				self.simpleStatement()
		except:
			print("continue parsing next statement\n")


	def simpleStatement(self):
		if self.token.code == Token.NULL:
			self.nullStatement()
		elif self.token.code == Token.EXIT:
			self.exitStatement()
		else:
			self.nameStatement()	# TODO: resolve comment: own method


	def nameStatement(self):
		# TODO: to invoke procedureStatement(), force <procedure>name
		# TODO: to invoke assignmentStatement(), force <variable>name
		self.name()
		if self.token.code == Token.COLON_EQ:
			self.assignmentStatement()
		else:
			self.procedureCallStatement()


	def compoundStatement(self):
		if self.token.code == Token.IF:
			self.ifStatement()
		else:
			self.loopStatement()


	def nullStatement(self):
		self.accept(Token.NULL,
					"null expected")
		self.accept(Token.SEMICOLON,
					"semicolon expected")


	def assignmentStatement(self):
		self.accept(Token.COLON_EQ,
					":= expected")
		self.expression()
		self.accept(Token.SEMICOLON,
					"semicolon expected")


	def ifStatement(self):
		self.accept(Token.IF,
					"if expected")
		self.condition()
		self.accept(Token.THEN,
					"then expected")
		self.sequenceOfStatements()
		while self.token.code == Token.ELSIF:
			self.token = self.scanner.GetNextToken()
			self.condition()
			self.accept(Token.THEN,
						"then expected")
			self.sequenceOfStatements()
		if self.token.code == Token.ELSE:
			self.token = self.scanner.GetNextToken()
			self.sequenceOfStatements()
		self.accept(Token.END,
					"end expected")
		self.accept(Token.IF,
					"if expected")
		self.accept(Token.SEMICOLON,
					"semicolon expected")


	def loopStatement(self):
		try:
			if self.token.code == Token.WHILE:
				self.iterationScheme()
			self.accept(Token.LOOP,
						"loop expected")
		except RuntimeError as e:
			print("continue parsing from sequence of statements of loop statement\n")

		self.sequenceOfStatements()

		try:
			self.accept(Token.END,
						"end expected")
			self.accept(Token.LOOP,
						"loop expected")
			self.accept(Token.SEMICOLON,
						"semicolon expected")
		except RuntimeError as e:
			print("stop parsing loop statement\n")


	def iterationScheme(self):
		self.accept(Token.WHILE,
					"while expected")
		self.condition()


	def exitStatement(self):
		self.accept(Token.EXIT,
					"exit expected")
		if self.token.code == Token.WHEN:
			self.token = self.scanner.GetNextToken()
			self.condition()
		self.accept(Token.SEMICOLON,
					"semicolon expected")


	def procedureCallStatement(self):
		if self.token.code == Token.PARENTHESIS_OPEN:
			self.actualParameterPart()
		self.accept(Token.SEMICOLON,
					"semicolon expected")


	def actualParameterPart(self):
		self.accept(Token.PARENTHESIS_OPEN,
					"open parenthesis expected")
		self.expression()
		while self.token.code == Token.COMMA:
			self.token = self.scanner.GetNextToken()
			self.expression()
		self.accept(Token.PARENTHESIS_CLOSE,
					"close parenthesis expected")


	def condition(self):
		self.expression() # TODO: force <boolean>expression


	def expression(self):
		self.relation()
		if self.token.code == Token.AND:
			while self.token.code == Token.AND:
				self.token = self.scanner.GetNextToken()
				self.relation()
		elif self.token.code == Token.OR:
			while self.token.code == Token.OR:
				self.token = self.scanner.GetNextToken()
				self.relation()


	def relation(self):
		self.simpleExpression()
		if self.token.code in Token.relationalOperator:
			self.token = self.scanner.GetNextToken()
			self.simpleExpression()


	def simpleExpression(self):
		if self.token.code in Token.addingOperator:
			self.token = self.scanner.GetNextToken()
		self.term()
		while self.token.code in Token.addingOperator:
			self.token = self.scanner.GetNextToken()
			self.term();


	def term(self):
		self.factor()
		while self.token in Token.multiplyingOperator:
			self.token = self.scanner.GetNextToken()
			self.factor()


	def factor(self):
		# not
		if self.token.code == Token.NOT:
			self.token = self.scanner.GetNextToken()
			self.primary()
		else:
			self.primary()
			if self.token.code == Token.SQUARE:
				self.token = self.scanner.GetNextToken()
				self.primary()


	def primary(self):
		if self.token.code in (Token.numericalLiteral, Token.stringLiteral):
			self.token = self.scanner.GetNextToken()
		elif self.token.code == Token.ID:
			self.name()
		elif self.token.code == Token.PARENTHESIS_OPEN:
			self.token = self.scanner.GetNextToken()
			self.expression()
			self.accept(Token.PARENTHESIS_CLOSE,
						"\')\' expected")
		else:
			self.fatalError("expected either a numeric literal, an identifier, or an opening parenthesis but " + 
				str(self.token) + " was detected")


	def name(self):
		self.accept(Token.ID,
					"identifier expected")
		if self.token.code == Token.PARENTHESIS_OPEN:	# TODO: resolve comment: indexedComponent
			self.indexedComponent()


	def indexedComponent(self):
		self.accept(Token.PARENTHESIS_OPEN,
					"\'(\' expected")
		self.expression()
		while self.token.code == Token.COMMA:
			self.token = self.scanner.GetNextToken()
			self.expression()
		self.accept(Token.PARENTHESIS_CLOSE,
					"\')\' expected")

		# TODO: resolve the following comment
		#모든 메소드를 호출하면 GetNextToken 이 자동으로 됨
		#따라서 메소드를 호출한 후에는 GetNextToken 사용 금지
		#함수를 호출하지 않고 종료되거나 다음 토큰을 봐야 할 경우 사용


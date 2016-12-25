import numpy as np
import math
import string
import copy

# This script implements a solution algorithm to the word ladder game (https://en.wikipedia.org/wiki/Word_ladder)
# In short: A pair of two words is given. In each turn it is allowed for one letter to be added or removed from the starting word,
# such that it is slowly changed into the second word. 
# Reshuffling the letters (permutations) is free, but it always has to be a valid word. 
#
# This script requires an external list of permissible words ("wordList.txt")
# Sample file contains 354986 English, non-compounded words (credits to github.com/dwyl for the list)
# 
# how to use: python laddder.py "firstword" "secondword"

# key ideas:
# permutations are free, i.e. the code can mostly work with word histograms
# words are addressed by their index in the original list
# the code implements a bidirectional A* graph search
# each node stores: its current histogram, a list of the words in its history, a reference to the mother search instance
# the heuristic is defined below as absolute distance between two histograms
# it is consistent: h(a) <= cost(a,b) + h(b), as the set of allowed (ladder) moves from 
# a to b is a subset of all differences

verbose_flag = 1 
# 0 = silent processing
# 1 = displays current arc via word indices
# 2 = displays current arc via words (look ups slow code down)


# convert string to its histogram, only letters allowed
def word_to_histogram(wordin):
	hist = np.zeros([1,26]) 
	for letter in wordin.lower():
		if letter.isalpha():
			tmp = ord(letter)-97
			hist[0,tmp] += 1
	return hist


# distance between two word
def heuristic(hist1,hist2):
	return np.sum(abs(hist1[0,:]-hist2[0,:]))


#returns the index of a word corresponding to its histogram, returns -1 if it does not exist
def hist_to_index(other_hist):
	for ind,hist in enumerate(wordlist):
		if np.all(hist == other_hist):
			return ind
	return -1


# load word list and extract histograms right away
# if already in memory this function is skipped
try:
	wordlist
except NameError:
	print("loading word file...")
	path  = "wordlist.txt"
	ffile = open(path,'r')
	words_original = []
	wordlist = []
	for line in ffile:
		line = line[:-1] #remove line break
		words_original.append(line)
		tmp = word_to_histogram(line)
		wordlist.extend(tmp)
	ffile.close()
	wordlist = np.array(wordlist)
	print("...done")
else:
	print("word file already in memory")



class Node:
	#Member variables are:
	#mygraph, reference to associated search 
	#current_hist, histogram associated with this node
	#cost_f, cost_h and cost_total, costs for this node: already performed moves, estimate for remaining number of moves
	#actions, a list of all words (their indices leading up to here), -1 = word is unchecked
	
	def __init__(self, mygraph0, other_Node = None):
		if other_Node == None:
			#generate new empty node, associated with graph
			self.mygraph = mygraph0
			self.current_hist = mygraph0.start_hist
			self.cost_f = 0		
			self.cost_h = heuristic(mygraph0.start_hist,mygraph0.target_hist)
			self.cost_total = self.cost_f + self.cost_h #total cost
			self.actions = [hist_to_index(self.mygraph.start_hist)] #index of all words up to here, -1 for unchecked words
		else:
			#copy constructor
			self.mygraph = mygraph0
			self.current_hist = other_Node.current_hist.copy()
			self.cost_f = other_Node.cost_f
			self.cost_h = other_Node.cost_h
			self.cost_total = self.cost_f + self.cost_h #total cost
			self.actions = other_Node.actions.copy()		
	
						
	#moves this node to a neighbouring node, give the index of new word as argument
	def move_to_neighbour(self,new_hist, new_index):
		self.current_hist = new_hist
		self.actions.append(new_index)
		self.cost_f = self.cost_f + 1
		self.cost_h = heuristic(self.current_hist,self.mygraph.target_hist)
		self.cost_total = self.cost_f + self.cost_h		
	

	def is_same_word(self, other):
		#is it the same histogram?
		return np.all(self.current_hist == other.current_hist)
	
	# checks whether given word is part of a given list
	def is_in_list(self,mylist):
		for nd in mylist:
			if self.is_same_word(nd):
				return nd
		return False		

	# fuses to nodes, is used in bidirectional search
	# the second node is assumed to have started from the target, i.e. its actions are flipped
	def attach(self, other):
		other.actions.reverse()
		self.actions.extend(other.actions)
		self.cost_f += other.cost_f
		self.cost_h = 0
		self.cost_total = self.cost_f + self.cost_h	
		
	def list_of_moves(self):
		#returns a list of all moves stored in actions
		#initial and target node are reset to input word, since the script only
		#might return their palindrome otherwise
		list_moves = []
		for index in self.actions:
			if (heuristic(wordlist[index,:].reshape(1,26),self.mygraph.start_hist)==0):
				list_moves.append(self.mygraph.start_word)
				continue
			if (heuristic(wordlist[index,:].reshape(1,26),self.mygraph.target_hist)==0):
				list_moves.append(self.mygraph.target_word)
				continue
			list_moves.append(words_original[index])
		return list_moves
			

	def display_moves(self):
		for word in self.list_of_moves():
			print(word)
	
	
	# the code needs to sort nodes by their total cost
	# I am using the native python sort algorithm and thus defined a total order on class nodes	
	def __ge__(self,other):
		return (self.cost_total >= other.cost_total)
		
	def __gt__(self,other):
		return (self.cost_total > other.cost_total)

	def __le__(self,other):
		return (self.cost_total <= other.cost_total)
		
	def __lt__(self,other):
		return (self.cost_total < other.cost_total)




class SearchGraph:
	# this class implements an A* graph search, unidirectional
	def __init__(self,start_word0, target_word0):
		self.start_word = start_word0 #strings of input words
		self.target_word = target_word0
		self.start_hist = word_to_histogram(start_word0)		
		self.target_hist = word_to_histogram(target_word0)
		self.frontier = [Node(self)]
		self.closed = []
		self.solution = None #the solution if found

	# one iteration
	def search_step(self):
		self.frontier.sort()
		test_node = self.frontier.pop(0)

		if test_node.cost_h==0:
			self.solution = test_node
			return test_node
		self.closed.append(test_node)	
		
		if verbose_flag == 1:
			print(test_node.actions)
		elif verbose_flag == 2:
			print(test_node.list_of_moves())	
		for new_index,row in enumerate(wordlist):
			next_hist = row.reshape([1,26])
			if heuristic(next_hist,test_node.current_hist)==1:
				new_node = Node(self,test_node)
				new_node.move_to_neighbour(next_hist,new_index)
				if not new_node.is_in_list(self.closed):
					tmp = new_node.is_in_list(self.frontier)
					if not tmp:
						self.frontier.append(new_node)
					else:
						if tmp > new_node: 
							#if new_node has lower cost, kick out 
							# already exiting node
							tmp = new_node
		return None

	def search(self):
		while len(self.frontier) > 0:
			nd = self.search_step()
			if nd != None:
				self.solution = nd
				return nd
		self.solution = None
		return None
		

#this class implements the bidirectional version 
#starting from initial word (north) and target word (south)
#and advancing each graph alternately
class BiSearchGraph:
	def __init__(self,start_word0, target_word0):
		self.north = SearchGraph(start_word0,target_word0)
		self.south = SearchGraph(target_word0,start_word0)
		self.solution = None
	
	def search(self):
		while (len(self.north.frontier) > 0) and (len(self.south.frontier) > 0) :
			nd_north =  self.north.search_step()
			if nd_north != None:
				self.solution = nd_north
				return nd_north			
			nd_tmp =  self.intersect()
			if nd_tmp != None:
				self.solution = nd_tmp
				return nd_tmp			
			nd_south =  self.south.search_step()
			if nd_south != None:
				self.solution = flip(nd_south)
				return nd_south	
			nd_tmp = self.intersect()	
			if nd_tmp != None:
				self.solution = nd_tmp
				return nd_tmp		
		self.solution = None
		return None		
	
	#checks if frontiers have intersected, if yes, fuse their nodes and we are done
	def intersect(self):
		for nd1 in self.north.frontier:
			for nd2 in self.south.frontier:
				if nd1.is_same_word(nd2):
					return nd1.attach(nd2)
		return None


### generate output files
import sys
if len(sys.argv) != 3:
	print("incorrect number of arguments")
	sys.exit()
start_word = sys.argv[1]
target_word = sys.argv[2]

A = BiSearchGraph(start_word,target_word)
node = A.search()
node.display_moves()

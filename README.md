Python Firebasin
================

Firebasin is a reimplementation of the [Firebase Javascript SDK](https://www.firebase.com/docs/javascript/firebase/index.html) in pure Python. Firebasin aims to have an interface identical to the Javascript SDK. As such, the Firebase Javascript docs can be used as temporary docs for Firebasin as the interface is identical. However, it should be noted that the implementation and internal structure of Firebasin differs greatly from the Javascript SDK. This is done intentionally as an attempt to implement things as pythonically as possible.

Compatibility List
-----
Firebase
*	Firebase( )			[DONE]
*	auth( )				[DONE]
*	unauth( )			[DONE]
*	child( )			[DONE]
*	parent( )			[DONE]
*	root( )				[DONE]
*	name( )				[DONE]
*	toString( )			[DONE]
*	set( )				[DONE]
*	update( )			[DONE]
*	remove( )			[DONE]
*	push( )				[DONE]
*	setWithPriority( )	[DONE]
*	setPriority( )		[DONE]
*	transaction( )		[	 ]
*	on( )				[DONE]
*	off( )				[	 ]
*	once( )				[	 ]
*	limit( )			[	 ]
*	startAt( )			[	 ]
*	endAt( )			[ 	 ]

Query
*	on( )				[DONE]
*	off( )				[	 ]
*	once( )				[	 ]
*	limit( )			[    ]
*	startAt( )			[    ]
*	endAt( )			[    ]

onDisconnect
*	set( )				[DONE]
*	setWithPriority( )	[DONE]
*	update( )			[DONE]
*	remove( )			[DONE]
*	cancel( )			[DONE]

DataSnapshot
*	val( )				[DONE]
*	child( )			[DONE]
*	forEach( )			[DONE]
*	hasChild( )			[DONE]
*	hasChildren( )		[DONE]
*	name( )				[DONE]
*	numChildren( )		[DONE]
*	ref( )				[	 ]
*	getPriority( )		[DONE]
*	exportVal( )		[DONE]
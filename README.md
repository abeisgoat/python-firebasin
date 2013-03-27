Python Firebasin
================

Firebasin is a reimplementation of the [Firebase Javascript SDK](https://www.firebase.com/docs/javascript/firebase/index.html) in pure Python. Firebasin aims to have an interface identical to the Javascript SDK. As such, the Firebase Javascript docs can be used as temporary docs for Firebasin as the interface is identical. However, it should be noted that the implementation and internal structure of Firebasin differs greatly from the Javascript SDK. This is done intentionally as an attempt to implement things as pythonically as possible.

Compatible Method List
-----
**Firebase**
* Firebase( )			
* auth( )				
* unauth( )				
* child( )				
* parent( )				
* root( )				
* name( )				
* toString( )			
* set( )				
* update( )				
* remove( )				
* push( )				
* setWithPriority( )	
* setPriority( )		
* transaction( )		
* on( )							

**onDisconnect**
* set( )				
* setWithPriority( )	
* update( )				
* remove( )				
* cancel( )				

**DataSnapshot**
* val( )				
* child( )				
* forEach( )			
* hasChild( )			
* hasChildren( )		
* name( )				
* numChildren( )					
* getPriority( )		
* exportVal( )			

Incompatible Method List
-----
**Firebase**			
* off( )				
* once( )				
* limit( )				
* startAt( )			
* endAt( )				

**DataSnapshot**
* ref( )				
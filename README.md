Python Firebasin 0.1
====================

*Please note: Very little testing has been done on Firebasin, it is considered experimental until future notice.*

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
* setWithPriority( )	
* setPriority( )		
* transaction( )		
* on( )	
* once( )		
* off( )
* limit( )				
* startAt( )			
* endAt( )								

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
* push( )											

**DataSnapshot**
* ref( )				
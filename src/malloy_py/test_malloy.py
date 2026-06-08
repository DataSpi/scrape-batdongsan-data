import asyncio
import nest_asyncio
import tempfile
import os

nest_asyncio.apply()
# test
async def main():
  print("[1] Starting...")
  try:
    import malloy
    from malloy.data.duckdb import DuckDbConnection
    
    print("[2] Creating runtime...")
    with malloy.Runtime() as runtime:
      runtime.add_connection(DuckDbConnection(home_dir="d:/scrape-batdongsan-data/", name="duckdb"))
      
      print("[3] Creating temp Malloy file...")
      # Create a temporary .malloy file with named query
      malloy_code = """
      source: real_estate is duckdb.table('data/real_estate_listings.csv')
      
      query: get_data is real_estate -> {
        select: product_id, price, bedrooms
        limit: 10
      }
      """
      
      # Write to temp file and load it
      with tempfile.NamedTemporaryFile(mode='w', suffix='.malloy', delete=False) as f:
        f.write(malloy_code)
        temp_file = f.name
      
      try:
        print("[4] Loading and running query...")
        source = runtime.load_file(temp_file)
        data = await source.run(named_query="get_data")  # Use named_query parameter
        
        print("[5] Success!")
        dataframe = data.to_dataframe()
        print(f"Rows: {len(dataframe)}\n")
        print(dataframe)
      finally:
        os.unlink(temp_file)  # Clean up temp file
      
  except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
  asyncio.run(main())
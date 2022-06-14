using System.Collections.Generic;
using ${project_name};
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Test.Loader;

[TestClass]
public class ArrayLoaderTests
{
    readonly ArrayLoader<int> testLoader = new(new PrimitiveLoader<int>());

    [TestMethod]
    public void TestLoad()
    {
        List<int> testValues = new() { 1, 2, 3, 4 };
        CollectionAssert.AreEqual(testValues, testLoader.Load(testValues, "", new LoadingOptions(), ""));
    }

    [TestMethod]
    public void TestExceptionNull()
    {
        try
        {
            testLoader.Load(null!, "", new LoadingOptions(), "");
        }
        catch (ValidationException e)
        {
            Assert.IsInstanceOfType(e, typeof(ValidationException));
            Assert.AreEqual("Expected non null", e.Message);
            return;
        }
        Assert.Fail("No ValidationException thrown");
    }

    [TestMethod]
    public void TestExceptionNoList()
    {
        try
        {
            testLoader.Load(1, "", new LoadingOptions(), "");
        }
        catch (ValidationException e)
        {
            Assert.IsInstanceOfType(e, typeof(ValidationException));
            Assert.AreEqual("Expected list", e.Message);
            return;
        }
        Assert.Fail("No ValidationException thrown");
    }
}
